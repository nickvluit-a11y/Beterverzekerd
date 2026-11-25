"""Turn extracted contract tables (from hospital PDFs and web pages) into normalised contract rows.

Hospitals publish their overviews in different layouts. This parser handles:
  * row-oriented:    | Zilveren Kruis | Gecontracteerd | Omzetplafond: ja |
    (a header row tells 'contract' columns from 'omzetplafond' columns; with a concern column
    and a label column, the more specific label wins)
  * column-oriented: header row of labels; status rows below, plus an optional 'Omzetplafond' row
  * no table at all:  text lines like 'Zilveren Kruis: gecontracteerd' (each line on its own)
A table that names only 'VGZ' (and no other VGZ labels) is read as speaking for the whole concern.

Everything is written with needs_review=True: a human confirms it against the source before it
goes into data/manual/contracts.csv.

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

from pipeline.contract_status import clean, combine, combine_plafond, plafond_from_text, status_from_text
from pipeline.reference import ROOT, find_labels, match_label, normalise, save_with_history

MONTHS = ("januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december"
          "|jan|feb|mrt|apr|jun|jul|aug|sept|sep|okt|nov|dec")
_DATE = re.compile(
    r"(?:peildatum|stand van zaken|situatie van|bijgewerkt|versie|datum|status)[^\n]{0,40}?"
    rf"\b(\d{{1,2}}[-/ ](?:\d{{1,2}}|(?:{MONTHS})\.?)[-/ ]\d{{4}})",
    re.IGNORECASE,
)
_YEAR = re.compile(r"\b(20[2-3]\d)\b")
_YEAR_CONTEXT = re.compile(r"contract|overzicht|zorgverzekeraar|onderhandel|polis", re.IGNORECASE)
_HEADER_WORDS = re.compile(r"verzekeraar|concern|label|contract|status|plafond|polis|\b20\d\d\b")
MAX_WORDS = 8  # longer cells are prose, not table values


def find_peildatum(text: str) -> str | None:
    match = _DATE.search(text)
    return match.group(1) if match else None


def find_year(text: str) -> int | None:
    """Contract year. Years on lines about contracts/insurers count first (most frequent,
    ties to the later year); without such lines, all years count."""
    context = [int(y) for line in text.splitlines() if _YEAR_CONTEXT.search(line) for y in _YEAR.findall(line)]
    years = context or [int(y) for y in _YEAR.findall(text)]
    if not years:
        return None
    counts = Counter(years)
    return max(counts, key=lambda y: (counts[y], y))


def _cell(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _is_prose(cell: str) -> bool:
    return len(cell.split()) > MAX_WORDS


def _pick_label(hits: list[tuple[int, tuple[str, str | None]]]) -> tuple[int, tuple[str, str | None]]:
    """Of several label cells in one row (e.g. 'VGZ | IZA'), the most specific one:
    a label whose name differs from its concern; otherwise the rightmost hit."""
    specific = [(i, h) for i, h in hits if h[1] and h[1] != h[0]]
    return (specific or hits)[-1]


def _concern_level(rows: list[dict]) -> list[dict]:
    """In a table that names only 'VGZ' (no other VGZ labels), 'VGZ' means the whole concern."""
    for row in rows:
        labels_of_concern = {r["label"] for r in rows if r["concern"] == row["concern"]}
        if row["label"] == row["concern"] and labels_of_concern <= {row["concern"], None}:
            row["label"] = None
    return rows


def _row(hit: tuple[str, str | None], status: str, plafond: bool | None, raw: str, polis: str | None = None) -> dict:
    return {"concern": hit[0], "label": hit[1], "polis": polis, "status": status, "omzetplafond": plafond, "raw": raw}


def _column_oriented(rows: list[list[str]]) -> list[dict]:
    header = [match_label(c) for c in rows[0]]
    out = []
    for col, hit in enumerate(header):
        if not hit:
            continue
        statuses, plafonds, raw = [], [], []
        for row in rows[1:]:
            if col >= len(row) or _is_prose(row[col]):
                continue
            is_plafond_row = "plafond" in clean(row[0])
            plafonds.append(plafond_from_text(row[col], plafond_column=is_plafond_row))
            if not is_plafond_row:
                statuses.append(status_from_text(row[col]))
            raw.append(row[col])
        status, plafond = combine(statuses), combine_plafond(plafonds)
        if status == "onbekend" and plafond:
            status = "gecontracteerd"
        if any(s != "onbekend" for s in statuses) or plafond is not None:
            out.append(_row(hit, status, plafond, " | ".join(raw)))
    return out


def _row_oriented(rows: list[list[str]]) -> list[dict]:
    first = rows[0]
    is_header = not any(match_label(c) for c in first) and any(_HEADER_WORDS.search(clean(c)) for c in first)
    plafond_cols = {i for i, c in enumerate(first) if "plafond" in clean(c)} if is_header else set()
    out = []
    for row in rows[1:] if is_header else rows:
        hits = [(i, h) for i, c in enumerate(row) if not _is_prose(c) and (h := match_label(c))]
        if not hits:
            continue
        label_cols = {i for i, _ in hits}
        _, hit = _pick_label(hits)
        statuses, plafonds, polis = [], [], None
        for j, cell in enumerate(row):
            if j in label_cols or not cell or _is_prose(cell):
                continue
            plafond = plafond_from_text(cell, plafond_column=j in plafond_cols)
            plafonds.append(plafond)
            if j in plafond_cols:
                continue
            status = status_from_text(cell)
            statuses.append(status)
            if status == "onbekend" and plafond is None and hit[1] and normalise(hit[1]) in normalise(cell):
                polis = cell  # e.g. 'VGZ Bewuzt': the row is about one policy, not the whole label
        status, plafond = combine(statuses), combine_plafond(plafonds)
        if status == "onbekend" and plafond:
            status = "gecontracteerd"
        if any(s != "onbekend" for s in statuses) or plafond is not None:
            # several concerns sharing one status cell ('Menzis | DSW: gecontracteerd') -> a row each
            targets = [h for _, h in hits] if len({h[0] for _, h in hits}) > 1 else [hit]
            out += [_row(t, status, plafond, " | ".join(row), polis) for t in targets]
    return out


def parse_tables(tables: list[list[list[object]]]) -> list[dict]:
    rows: list[dict] = []
    for table in tables:
        clean_rows = [[_cell(c) for c in row] for row in table if row]
        clean_rows = [r for r in clean_rows if any(r)]
        if not clean_rows:
            continue
        if len(clean_rows) > 1 and sum(match_label(c) is not None for c in clean_rows[0]) >= 2:
            rows += _concern_level(_column_oriented(clean_rows))
        else:
            rows += _concern_level(_row_oriented(clean_rows))
    return rows


_STATUS_AT_END = re.compile(
    r"(\(?nog\)? geen contract|niet gecontracteerd|gecontracteerd|in onderhandeling|onderhandelingen lopen|"
    r"geen contract|contract afgesloten)\b.*$", re.IGNORECASE)
MAX_LINE_WORDS = 16


def parse_lines(text: str) -> list[dict]:
    """Rows from text lines like 'VGZ Univé In onderhandeling' or 'Zilveren Kruis: gecontracteerd met
    omzetplafond': a status phrase at the end, insurer names before it. The most specific label in the
    line wins ('VGZ Univé' -> Univé; 'DSW DSW' -> DSW)."""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line or len(line.split()) > MAX_LINE_WORDS:
            continue
        match = _STATUS_AT_END.search(line)
        if not match:
            continue
        names = find_labels(line[:match.start()])
        if not names:
            continue
        specific = [n for n in names if n[1] and n[1] != n[0]]
        hit = (specific or names)[-1]
        status = status_from_text(match.group(0))
        plafond = plafond_from_text(match.group(0))
        if status != "onbekend":
            rows.append(_row(hit, status, plafond, line))
    return _concern_level(rows)


_LEGEND = re.compile(r"^\s*(\d)\s*[:=–-]\s*(.{3,120})$")


def parse_legend(text: str) -> list[dict]:
    """Overviews that code the status as a digit with a legend, e.g. '4: we hebben een contract',
    '0: wij hebben geen contract', followed by rows 'label / concern / 2 / 4' on separate lines.
    The first digit after a label belongs to the first (newest) status column."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    legend = {}
    for line in lines:
        match = _LEGEND.match(line)
        if match:
            status = status_from_text(match.group(2))
            if status != "onbekend":
                legend[match.group(1)] = status
    if len(legend) < 2:
        return []
    rows, pending = [], []
    for line in lines:
        if line in legend:
            if pending:
                specific = [n for n in pending if n[1] and n[1] != n[0]]
                hit = (specific or pending)[-1]
                rows.append(_row(hit, legend[line], None, " | ".join(map(str, pending)) + f" | {line}"))
                pending = []
            continue
        if _LEGEND.match(line) or len(line.split()) > MAX_LINE_WORDS:
            continue
        pending += find_labels(line)
    return _concern_level(rows)


def line_tables(text: str) -> list[list[list[str]]]:
    """Fallback for text without tables: every line becomes its own one-row table, split on
    ':', '|', dashes, tabs or wide gaps. No header semantics carry over between lines."""
    tables = []
    for line in text.splitlines():
        cells = [c for c in re.split(r"\s*[:|\t–—]\s*|\s+-\s+|\s{2,}", line.strip()) if c]
        if len(cells) >= 2:
            tables.append([cells])
    return tables


def parse_source(tables: list, text: str) -> list[dict]:
    """Rows from tables, plus rows from text lines for labels the tables missed."""
    parsed = parse_tables(tables)
    for extra in (parse_legend(text), parse_lines(text), parse_tables(line_tables(text))):
        seen = {(r["concern"], r["label"]) for r in parsed}
        parsed += [r for r in extra if (r["concern"], r["label"]) not in seen]
    return parsed


def latest_raw_dir() -> Path | None:
    base = ROOT / "data" / "raw" / "contracts"
    dirs = sorted(p for p in base.glob("*") if p.is_dir()) if base.exists() else []
    return dirs[-1] if dirs else None


COLUMNS = ["year", "organisatie_agb", "location_id", "concern", "label", "polis", "status", "omzetplafond", "peildatum",
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
        organisation = info.get("organisatie_agb")
        location_ids = info.get("location_ids") or ([None] if organisation else [key])
        try:
            text = (source_dir / f"{key}.txt").read_text(encoding="utf-8")
            parsed = parse_source(json.loads(tables_file.read_text(encoding="utf-8")), text)
        except Exception as exc:  # one odd page must not lose the other hospitals
            print(f"FAIL {key}: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        year, peildatum = find_year(text), find_peildatum(text)
        for location_id in location_ids:  # one source can cover several locations
            for row in parsed:
                out_rows.append({**row, "location_id": location_id, "organisatie_agb": organisation,
                                 "year": year, "peildatum": peildatum,
                                 "source": f"contracts_{info.get('format', 'pdf')}", "source_url": info.get("url"),
                                 "fetched_on": source_dir.name, "needs_review": True})
        print(f"{key}: {len(parsed)} contract rows")
    save_with_history(pd.DataFrame(out_rows, columns=COLUMNS), "contracts_candidates", source_dir.name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
