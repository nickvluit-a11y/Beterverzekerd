"""Extract waiting times for our specialisms from the NZa CSV.

1. Describe the CSV -> docs/data_inventory/nza_wachttijden.md (committed).
2. Keep rows whose specialism matches a procedure's nza_pattern.
3. Write data/processed/waiting_times.csv (one row per location × specialism × type × peildatum).

Usage: python -m pipeline.nza_ingest [raw_dir]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

from pipeline.reference import PROCESSED, ROOT, match_location, procedures
from pipeline.tabular import describe, find_column, read_any

INVENTORY = ROOT / "docs" / "data_inventory" / "nza_wachttijden.md"
COLUMN_PATTERNS = {
    "provider": (r"naam.*(locatie|vestiging)", r"locatie.*naam", r"naam.*instelling", r"instelling.*naam", r"naam"),
    "agb": (r"agb.*(locatie|vestiging)", r"agb",),
    "kvk": (r"kvk",),
    "city": (r"plaats",),
    "postcode": (r"postcode",),
    "specialism": (r"specialisme.*(omschr|naam)", r"specialisme", r"zorgspecialisme"),
    "wait_type": (r"type.*wacht", r"wachttijd.*type", r"soort"),
    "weeks": (r"wachttijd.*week", r"^wachttijd$", r"wachttijd"),
    "peildatum": (r"peildatum", r"datum"),
}


def latest_raw_dir() -> Path | None:
    base = ROOT / "data" / "raw" / "nza_wachttijden"
    dirs = sorted(p for p in base.glob("*") if p.is_dir()) if base.exists() else []
    return dirs[-1] if dirs else None


def extract(df: pd.DataFrame, fetched_on: str, source_url: str | None) -> pd.DataFrame:
    cols = {k: find_column(df, *p, required=k in {"provider", "specialism", "weeks"}) for k, p in COLUMN_PATTERNS.items()}
    if cols["weeks"] == cols["wait_type"]:
        cols["wait_type"] = None
    parts = []
    for proc in procedures().itertuples():
        mask = df[cols["specialism"]].fillna("").str.contains(proc.nza_pattern, flags=re.IGNORECASE, regex=True)
        sub = df[mask]
        if sub.empty:
            continue
        parts.append(pd.DataFrame({
            "procedure_id": proc.procedure_id,
            "provider_raw": sub[cols["provider"]],
            "agb_code": sub[cols["agb"]] if cols["agb"] else None,
            "kvk": sub[cols["kvk"]] if cols["kvk"] else None,
            "city_raw": sub[cols["city"]] if cols["city"] else None,
            "postcode": sub[cols["postcode"]] if cols["postcode"] else None,
            "specialism": sub[cols["specialism"]],
            "wait_type": sub[cols["wait_type"]] if cols["wait_type"] else None,
            "weeks": pd.to_numeric(sub[cols["weeks"]].str.replace(",", ".", regex=False), errors="coerce"),
            "peildatum": sub[cols["peildatum"]] if cols["peildatum"] else None,
        }))
    if not parts:
        return pd.DataFrame()
    result = pd.concat(parts, ignore_index=True)
    result["location_id"] = [
        match_location(n, city=c if isinstance(c, str) else None, agb_code=a if isinstance(a, str) else None)
        for n, c, a in zip(result["provider_raw"], result["city_raw"], result["agb_code"])
    ]
    result["source"] = "nza_wachttijden"
    result["source_url"] = source_url
    result["fetched_on"] = fetched_on
    return result


def main(argv: list[str]) -> int:
    source_dir = Path(argv[0]) if argv else latest_raw_dir()
    if not source_dir:
        print("No raw NZa data; run scrapers.nza_wachttijden first.", file=sys.stderr)
        return 1
    meta_path = source_dir / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    tables = read_any(source_dir / "wachttijden.csv")
    pattern = "|".join(procedures()["nza_pattern"])
    INVENTORY.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY.write_text(describe(tables, f"NZa wachttijden msz ({source_dir.name})", pattern), encoding="utf-8")
    print(f"inventory: {INVENTORY}")
    df = next(iter(tables.values()))
    waits = extract(df, source_dir.name, meta.get("url"))
    if waits.empty:
        print("No rows for our specialisms; see the inventory and adjust COLUMN_PATTERNS.", file=sys.stderr)
        return 1
    PROCESSED.mkdir(parents=True, exist_ok=True)
    waits.to_csv(PROCESSED / "waiting_times.csv", index=False)
    print(f"waiting_times.csv: {len(waits)} rows, {waits['location_id'].notna().mean():.0%} matched to hospitals.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
