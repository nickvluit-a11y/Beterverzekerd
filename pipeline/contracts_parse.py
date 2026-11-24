"""Turn extracted contract-PDF tables into normalised contract rows.

Hospitals publish their tables in different layouts. This parser handles the two common ones:
  * row-oriented:    | Zilveren Kruis | Gecontracteerd (omzetplafond) |
  * column-oriented: header row of labels, status cells below it
Everything it finds is written with needs_review=True: a human (or a hospital-specific
parser) confirms it before it goes into data/manual/contracts.csv.

Usage: python -m pipeline.contracts_parse [raw_dir]
Output: data/processed/contracts_candidates.csv
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

from pipeline.contract_status import normalise_status
from pipeline.reference import PROCESSED, ROOT, match_label

_DATE = re.compile(
    r"(?:peildatum|stand van zaken|bijgewerkt|versie|datum)[^0-9]{0,20}"
    r"(\d{1,2}[-/ ](?:\d{1,2}|januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)[-/ ]\d{4})",
    re.IGNORECASE,
)
_YEAR = re.compile(r"\b(20[2-3]\d)\b")


def find_peildatum(text: str) -> str | None:
    match = _DATE.search(text)
    return match.group(1) if match else None


def find_year(text: str) -> int | None:
    """Contract year: the highest year mentioned (overviews are for the coming year; the peildatum is earlier)."""
    years = [int(y) for y in _YEAR.findall(text)]
    return max(years) if years else None


def parse_tables(tables: list[list[list[str | None]]]) -> list[dict]:
    rows: list[dict] = []
    for table in tables:
        clean = [[(c or "").strip() for c in row] for row in table if row]
        # Row-oriented: a label in one cell, status in another cell of the same row
        for row in clean:
            for i, cell in enumerate(row):
                hit = match_label(cell)
                if not hit:
                    continue
                others = " ".join(c for j, c in enumerate(row) if j != i)
                status, plafond = normalise_status(others)
                if status != "onbekend":
                    rows.append({"concern": hit[0], "label": hit[1], "status": status,
                                 "omzetplafond": plafond, "raw": " | ".join(row)})
                break
        # Column-oriented: header with >= 2 labels, statuses in the next rows
        if clean:
            header = [match_label(c) for c in clean[0]]
            if sum(h is not None for h in header) >= 2:
                for row in clean[1:]:
                    for hit, cell in zip(header, row):
                        if hit:
                            status, plafond = normalise_status(cell)
                            if status != "onbekend":
                                rows.append({"concern": hit[0], "label": hit[1], "status": status,
                                             "omzetplafond": plafond, "raw": cell})
    return rows


def latest_raw_dir() -> Path | None:
    base = ROOT / "data" / "raw" / "contracts_pdf"
    dirs = sorted(p for p in base.glob("*") if p.is_dir()) if base.exists() else []
    return dirs[-1] if dirs else None


def main(argv: list[str]) -> int:
    source_dir = Path(argv[0]) if argv else latest_raw_dir()
    if not source_dir:
        print("No raw contract PDFs found; run scrapers.contract_pdfs first.", file=sys.stderr)
        return 1
    meta = json.loads((source_dir / "meta.json").read_text(encoding="utf-8"))
    out_rows = []
    for tables_file in sorted(source_dir.glob("*.tables.json")):
        location_id = tables_file.name.removesuffix(".tables.json")
        text = (source_dir / f"{location_id}.txt").read_text(encoding="utf-8")
        parsed = parse_tables(json.loads(tables_file.read_text(encoding="utf-8")))
        for row in parsed:
            row.update(location_id=location_id, year=find_year(text), peildatum=find_peildatum(text),
                       source="contracts_pdf", source_url=meta["results"].get(location_id, {}).get("url"),
                       fetched_on=source_dir.name, needs_review=True)
        print(f"{location_id}: {len(parsed)} contract rows")
        out_rows += parsed
    PROCESSED.mkdir(parents=True, exist_ok=True)
    columns = ["year", "location_id", "concern", "label", "status", "omzetplafond", "peildatum",
               "source", "source_url", "fetched_on", "needs_review", "raw"]
    pd.DataFrame(out_rows, columns=columns).to_csv(PROCESSED / "contracts_candidates.csv", index=False)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
