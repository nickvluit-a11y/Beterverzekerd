"""Extract hip/knee/cataract indicators from the Zorginzicht MSZ open-data files.

Steps:
1. Describe every table in the latest raw download -> docs/data_inventory/zorginzicht.md
   (committed, so column names can be checked without downloading the files).
2. Find rows whose indicator text matches a procedure pattern from data/manual/procedures.csv.
3. Write data/processed/quality.csv in long format.

Column detection is by name pattern. When the real files use other names, the script
stops with the list of actual columns: adjust COLUMN_PATTERNS below.

Usage: python -m pipeline.zorginzicht_ingest [raw_dir]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

from pipeline.reference import PROCESSED, ROOT, match_location, procedures
from pipeline.tabular import describe, find_column, read_any

INVENTORY = ROOT / "docs" / "data_inventory" / "zorginzicht.md"
COLUMN_PATTERNS = {
    "provider": (r"naam.*(locatie|instelling|aanbieder|organisatie|zorgaanbieder)", r"^(locatie|instelling|organisatie|zorgaanbieder)", r"naam"),
    "agb": (r"agb",),
    "city": (r"plaats|woonplaats|vestigingsplaats",),
    "indicator_set": (r"indicatorset|meetinstrument|kwaliteitsinstrument|^set",),
    "indicator": (r"indicator(?!set)|vraag|omschrijving",),
    "value": (r"^waarde|score|uitkomst|antwoord|percentage|resultaat",),
    "numerator": (r"teller",),
    "denominator": (r"noemer",),
    "year": (r"verslagjaar|jaar",),
}


def latest_raw_dir() -> Path | None:
    base = ROOT / "data" / "raw" / "zorginzicht"
    dirs = sorted(p for p in base.glob("*") if p.is_dir()) if base.exists() else []
    return dirs[-1] if dirs else None


def extract(df: pd.DataFrame, table_name: str, fetched_on: str) -> pd.DataFrame:
    cols = {key: find_column(df, *pats, required=key in {"provider", "indicator"})
            for key, pats in COLUMN_PATTERNS.items()}
    set_col, ind_col = cols["indicator_set"], cols["indicator"]
    search_text = df[ind_col].fillna("")
    if set_col:
        search_text = df[set_col].fillna("") + " | " + search_text
    parts = []
    for proc in procedures().itertuples():
        mask = search_text.str.contains(proc.zorginzicht_pattern, flags=re.IGNORECASE, regex=True)
        if not mask.any():
            continue
        sub = df[mask]
        out = pd.DataFrame({
            "procedure_id": proc.procedure_id,
            "provider_raw": sub[cols["provider"]],
            "agb_code": sub[cols["agb"]] if cols["agb"] else None,
            "city_raw": sub[cols["city"]] if cols["city"] else None,
            "indicator_set": sub[set_col] if set_col else None,
            "indicator": sub[ind_col],
            "value": sub[cols["value"]] if cols["value"] else None,
            "numerator": sub[cols["numerator"]] if cols["numerator"] else None,
            "denominator": sub[cols["denominator"]] if cols["denominator"] else None,
            "verslagjaar": sub[cols["year"]] if cols["year"] else _year_from(table_name),
        })
        parts.append(out)
    if not parts:
        return pd.DataFrame()
    result = pd.concat(parts, ignore_index=True)
    result["location_id"] = [
        match_location(n, city=c if isinstance(c, str) else None, agb_code=a if isinstance(a, str) else None)
        for n, c, a in zip(result["provider_raw"], result["city_raw"], result["agb_code"])
    ]
    result["source"] = f"zorginzicht:{table_name}"
    result["fetched_on"] = fetched_on
    return result


def _year_from(name: str) -> str | None:
    match = re.search(r"20\d\d", name)
    return match.group(0) if match else None


def main(argv: list[str]) -> int:
    source_dir = Path(argv[0]) if argv else latest_raw_dir()
    if not source_dir:
        print("No raw Zorginzicht data; run scrapers.zorginzicht first.", file=sys.stderr)
        return 1
    tables: dict[str, pd.DataFrame] = {}
    for path in sorted(source_dir.iterdir()):
        if path.suffix.lower() in {".xlsx", ".xls", ".csv", ".zip"}:
            for name, df in read_any(path).items():
                tables[f"{path.name}:{name}"] = df
    pattern = "|".join(procedures()["zorginzicht_pattern"])
    INVENTORY.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY.write_text(describe(tables, f"Zorginzicht MSZ open data ({source_dir.name})", pattern), encoding="utf-8")
    print(f"inventory: {INVENTORY}")

    results, errors = [], []
    for name, df in tables.items():
        try:
            part = extract(df, name, source_dir.name)
        except KeyError as exc:
            errors.append(f"{name}: {exc}")
            continue
        if not part.empty:
            results.append(part)
            print(f"{name}: {len(part)} rows for our procedures")
    for error in errors:
        print(f"skipped {error}", file=sys.stderr)
    if not results:
        print("No matching indicator rows; see the inventory and adjust COLUMN_PATTERNS.", file=sys.stderr)
        return 1
    quality = pd.concat(results, ignore_index=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    quality.to_csv(PROCESSED / "quality.csv", index=False)
    matched = quality["location_id"].notna().mean()
    print(f"quality.csv: {len(quality)} rows, {matched:.0%} matched to hospitals.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
