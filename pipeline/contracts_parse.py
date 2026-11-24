"""Turn extracted contract tables (from hospital PDFs and web pages) into normalised contract rows.

Hospitals publish their tables in different layouts. This parser handles the two common ones:
  * row-oriented:    | Zilveren Kruis | Gecontracteerd | Omzetplafond: ja |
    (a header row is used to tell 'contract' columns from 'omzetplafond' columns)
  * column-oriented: header row of labels, status cells below it
  * no table at all:  text lines like 'Zilveren Kruis: gecontracteerd' (fallback)
Everything it finds is written with needs_review=True: a human (or a hospital-specific
parser) confirms it before it goes into data/manual/contracts.csv.

Usage: python -m pipeline.contracts_parse [raw_dir]
Output: data/processed/contracts_candidates.csv (+ dated copy under data/processed/history/)
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from pipeline.contract_status import clean, combine, plafond_from_text, status_from_text
from pipeline.reference import PROCESSED, ROOT, match_label, save_with_history

MONTHS = "januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december"
_DATE = re.compile(
    r"(?:peildatum|stand van zaken|bijgewerkt|versie|datum|status)[^0-9]{0,30}"
    rf"(\d{{1,2}}[-/ ](?:\d{{1,2}}|{MONTHS})[-/ ]\d{{4}})",
    re.IGNORECASE,
)
_YEAR = re.compile(r"\b(20[2-3]\d)\b")


def find_peildatum(text: str) -> str | None:
    match = _DATE.search(text)
    return match.group(1) if match else None


def find_year(text: str) -> int | None:
    """Contract year: the most frequently mentioned year; ties go to the later year
    (overviews are about the coming year, the peildatum lies in the year before)."""
    counts = Counter(int(y) for y in _YEAR.findall(text))
    if not counts:
        return None
    return max(counts, key=lambda y: (counts[y], y))


def _is_plafond_header(cell: str) -> bool:
    return "plafond" in clean(cell)


def parse_tables(tables: list[list[list[str | None]]]) -> list[dict]:
    rows: list[dict] = []
    for table in tables:
        clean_rows = [[(c or "").strip() for c in row] for row in table if row]
        if not clean_rows:
            continue
        header = clean_rows[0]
        header_labels = [match_label(c) for c in header]

        # Column-oriented: header with >= 2 labels, statuses in the rows below
        if sum(h is not None for h in header_labels) >= 2:
            for row in clean_rows[1:]:
                for hit, cell in zip(header_labels, row):
                    if hit:
                        status = status_from_text(cell)
                        plafond = plafond_from_text(cell)
                        if status == "onbekend" and plafond:
                            status = "gecontracteerd"
                        if status != "onbekend":
                            rows.append(_row(hit, status, plafond, cell))
            continue

        # Row-oriented: a label in one cell; other cells are contract or plafond columns
        plafond_cols = {i for i, c in enumerate(header) if _is_plafond_header(c)}
        for row in clean_rows:
            for i, cell in enumerate(row):
                hit = match_label(cell)
                if not hit:
                    continue
                others = [(j, c) for j, c in enumerate(row) if j != i and c]
                statuses = [status_from_text(c) for j, c in others if j not in plafond_cols]
                plafonds = [plafond_from_text(c, plafond_column=j in plafond_cols) for j, c in others]
                status = combine(statuses)
                known = {p for p in plafonds if p is not None}
                plafond = known.pop() if len(known) == 1 else None
                if status == "onbekend" and plafond:
                    status = "gecontracteerd"
                if status != "onbekend" or any(s != "onbekend" for s in statuses):
                    # conflicting cells are kept as 'onbekend' so they show up for review
                    rows.append(_row(hit, status, plafond, " | ".join(row)))
                break
    return rows


def _row(hit: tuple[str, str | None], status: str, plafond: bool | None, raw: str) -> dict:
    return {"concern": hit[0], "label": hit[1], "status": status, "omzetplafond": plafond, "raw": raw}


def line_tables(text: str) -> list[list[list[str]]]:
    """Fallback for pages without tables: each text line split on ':', '|', dashes, tabs or wide gaps."""
    rows = [re.split(r"\s*[:|\t–—]\s*|\s+-\s+|\s{2,}", line.strip()) for line in text.splitlines() if line.strip()]
    return [[row for row in rows if len(row) >= 2]]


def latest_raw_dir() -> Path | None:
    base = ROOT / "data" / "raw" / "contracts"
    dirs = sorted(p for p in base.glob("*") if p.is_dir()) if base.exists() else []
    return dirs[-1] if dirs else None


COLUMNS = ["year", "location_id", "concern", "label", "status", "omzetplafond", "peildatum",
           "source", "source_url", "fetched_on", "needs_review", "raw"]


def main(argv: list[str]) -> int:
    source_dir = Path(argv[0]) if argv else latest_raw_dir()
    if not source_dir:
        print("No raw contract pages found; run scrapers.contracts first.", file=sys.stderr)
        return 1
    meta = json.loads((source_dir / "meta.json").read_text(encoding="utf-8"))
    out_rows = []
    for tables_file in sorted(source_dir.glob("*.tables.json")):
        key = tables_file.name.removesuffix(".tables.json")
        info = meta["results"].get(key, {})
        location_ids = info.get("location_ids") or [key]
        text = (source_dir / f"{key}.txt").read_text(encoding="utf-8")
        parsed = parse_tables(json.loads(tables_file.read_text(encoding="utf-8")))
        seen = {(r["concern"], r["label"]) for r in parsed}
        # text lines add labels the tables missed (pages often mix a table with bullet lists)
        parsed += [r for r in parse_tables(line_tables(text)) if (r["concern"], r["label"]) not in seen]
        for location_id in location_ids:  # one PDF can cover several locations
            for row in parsed:
                out_rows.append({**row, "location_id": location_id, "year": find_year(text),
                                 "peildatum": find_peildatum(text), "source": f"contracts_{info.get('format', 'pdf')}",
                                 "source_url": info.get("url"), "fetched_on": source_dir.name,
                                 "needs_review": True})
        print(f"{key}: {len(parsed)} contract rows × {len(location_ids)} location(s)")
    save_with_history(pd.DataFrame(out_rows, columns=COLUMNS), "contracts_candidates", source_dir.name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
