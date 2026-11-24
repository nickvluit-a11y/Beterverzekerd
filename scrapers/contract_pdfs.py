"""Download hospital contract overviews (PDF) listed in data/manual/hospitals.csv.

For every location with a `contracts_url`, downloads the PDF once per organisation and
extracts text and tables with pdfplumber. Output per organisation:
data/raw/contracts_pdf/<today>/<location_id>.pdf / .txt / .tables.json + meta.json

One failing hospital does not stop the others.
Usage: python -m scrapers.contract_pdfs
"""

from __future__ import annotations

import io
import json
import sys

import pandas as pd
import pdfplumber

from scrapers.common import ROOT, PoliteSession, raw_dir, write_meta


def extract(pdf_bytes: bytes) -> tuple[str, list[list[list[str | None]]]]:
    texts, tables = [], []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            texts.append(page.extract_text() or "")
            tables += page.extract_tables()
    return "\n\n".join(texts), tables


def main() -> int:
    table = pd.read_csv(ROOT / "data" / "manual" / "hospitals.csv")
    targets = table.dropna(subset=["contracts_url"]).drop_duplicates("contracts_url")
    if targets.empty:
        print("No contracts_url filled in hospitals.csv")
        return 0
    http = PoliteSession()
    out = raw_dir("contracts_pdf")
    results, failures = {}, 0
    for row in targets.itertuples():
        try:
            resp = http.get(row.contracts_url)
            (out / f"{row.location_id}.pdf").write_bytes(resp.content)
            text, tables = extract(resp.content)
            (out / f"{row.location_id}.txt").write_text(text, encoding="utf-8")
            (out / f"{row.location_id}.tables.json").write_text(
                json.dumps(tables, ensure_ascii=False, indent=1), encoding="utf-8")
            results[row.location_id] = {"url": row.contracts_url, "tables": len(tables), "ok": True}
            print(f"ok   {row.location_id}: {len(tables)} tables")
        except Exception as exc:  # keep going for the other hospitals
            failures += 1
            results[row.location_id] = {"url": row.contracts_url, "ok": False, "error": str(exc)}
            print(f"FAIL {row.location_id}: {exc}", file=sys.stderr)
    write_meta(out, source="contracts_pdf", results=results)
    return 1 if failures == len(targets) else 0


if __name__ == "__main__":
    sys.exit(main())
