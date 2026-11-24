"""Extract hip/knee/cataract indicators from the Zorginzicht MSZ open-data files.

Steps:
1. Describe every table in the latest raw download -> docs/data_inventory/zorginzicht.md
   (committed, so column names can be checked without downloading the files).
2. Find rows whose indicator text matches a procedure pattern from data/manual/procedures.csv
   (indicator name first; the indicator-set name only for rows the indicator name leaves unmatched).
3. Write data/processed/quality.csv in long format (+ dated copy under history/).

Column detection is by name pattern. When the real files use other names, the table is
skipped with the list of actual columns: adjust COLUMN_PATTERNS below.

Usage: python -m pipeline.zorginzicht_ingest [raw_dir]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

from pipeline.reference import ROOT, match_location, procedures, save_with_history
from pipeline.tabular import describe, find_column, read_any

INVENTORY = ROOT / "docs" / "data_inventory" / "zorginzicht.md"
_CODE = r"agb|code|nummer|(?:^|[_\s])(?:nr|id)(?:$|[_\s])"
# key: (patterns tried in order, exclude-regex)
COLUMN_PATTERNS: dict[str, tuple[tuple[str, ...], str | None]] = {
    "provider": ((r"(locatie|instelling|organisatie|zorgaanbieder|aanbieder)\s*naam",
                  r"naam.*(locatie|instelling|organisatie|zorgaanbieder|aanbieder)",
                  r"^(locatie|instelling|organisatie|zorgaanbieder)$"), _CODE),
    "agb": ((r"agb",), None),
    "city": ((r"plaats",), None),
    "indicator_set": ((r"indicator\s*set", r"meetinstrument|kwaliteitsinstrument"), None),
    "indicator": ((r"indicator\s*(naam|omschrijving|titel)", r"^indicator$", r"vraag"), r"set|code|nummer|(?:^|[_\s])id(?:$|[_\s])"),
    "value": ((r"^waarde", r"score", r"uitkomst", r"antwoord", r"percentage", r"resultaat"), None),
    "numerator": ((r"teller",), None),
    "denominator": ((r"noemer",), None),
    "year": ((r"verslagjaar", r"^jaar$", r"jaar"), r"aanlever"),
}
REQUIRED = {"provider", "indicator"}


def latest_raw_dir() -> Path | None:
    base = ROOT / "data" / "raw" / "zorginzicht"
    dirs = sorted(p for p in base.glob("*") if p.is_dir()) if base.exists() else []
    return dirs[-1] if dirs else None


def detect_columns(df: pd.DataFrame) -> dict[str, str | None]:
    cols = {key: find_column(df, *pats, exclude=excl, required=key in REQUIRED)
            for key, (pats, excl) in COLUMN_PATTERNS.items()}
    if cols["provider"] == cols["indicator"]:
        raise KeyError(f"provider and indicator resolve to the same column {cols['provider']!r} "
                       "(probably a definitions sheet)")
    return cols


def assign_procedures(indicator: pd.Series, indicator_set: pd.Series | None) -> pd.Series:
    """procedure_id per row, or NA.

    A row gets a procedure only when exactly one pattern matches. The indicator text decides;
    the set name is used only for rows whose indicator text matches no pattern at all.
    Rows matching several procedures (e.g. 'heup- en knieprothese') stay NA for manual review.
    """
    def single_hit(text: pd.Series) -> tuple[pd.Series, pd.Series]:
        hits = pd.DataFrame({p.procedure_id: text.fillna("").str.contains(p.zorginzicht_pattern, flags=re.IGNORECASE, regex=True)
                             for p in procedures().itertuples()})
        count = hits.sum(axis=1)
        chosen = hits.idxmax(axis=1).where(count == 1)
        return chosen, count

    result, count = single_hit(indicator)
    if indicator_set is not None:
        from_set, _ = single_hit(indicator_set)
        result = result.where(count > 0, from_set)
    return result


def extract(df: pd.DataFrame, table_name: str, fetched_on: str) -> pd.DataFrame:
    cols = detect_columns(df)
    proc = assign_procedures(df[cols["indicator"]], df[cols["indicator_set"]] if cols["indicator_set"] else None)
    sub = df[proc.notna()]
    if sub.empty:
        return pd.DataFrame()

    def col(key: str):
        return sub[cols[key]] if cols[key] else None

    out = pd.DataFrame({
        "procedure_id": proc[proc.notna()],
        "provider_raw": col("provider"), "agb_code": col("agb"), "city_raw": col("city"),
        "indicator_set": col("indicator_set"), "indicator": col("indicator"),
        "value": col("value"), "numerator": col("numerator"), "denominator": col("denominator"),
        "verslagjaar": col("year") if cols["year"] else _year_from(table_name),
    }).reset_index(drop=True)
    out["location_id"] = [match_location(n, city=c, agb_code=a)
                          for n, c, a in zip(out["provider_raw"], out["city_raw"], out["agb_code"])]
    out["source"] = f"zorginzicht:{table_name}"
    out["fetched_on"] = fetched_on
    return out


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

    results = []
    for name, df in tables.items():
        try:
            part = extract(df, name, source_dir.name)
        except KeyError as exc:
            print(f"skipped {name}: {exc}", file=sys.stderr)
            continue
        if not part.empty:
            results.append(part)
            print(f"{name}: {len(part)} rows for our procedures")
    if not results:
        print("No matching indicator rows; see the inventory and adjust COLUMN_PATTERNS.", file=sys.stderr)
        return 1
    quality = pd.concat(results, ignore_index=True)
    save_with_history(quality, "quality", source_dir.name)
    print(f"quality.csv: {len(quality)} rows, {quality['location_id'].notna().mean():.0%} matched to hospitals.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
