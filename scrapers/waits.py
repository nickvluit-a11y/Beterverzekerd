"""Download the waiting-time pages hospitals publish on their own websites (an NZa obligation).

Sources: data/manual/waittime_sources.csv (organisatie_agb, wachttijden_url). Pages that link to a
dated PDF are followed. The extracted text is kept in docs/data_inventory/wachttijden/<agb>.txt
so the parser (pipeline/waits_parse.py) can be built and checked against the real pages.

Usage: python -m scrapers.waits
"""

from __future__ import annotations

import json
import re
import sys

import pandas as pd

from scrapers.common import ROOT, PoliteSession, all_links, raw_dir, today, write_meta
from scrapers.contracts import decode_html, extract_html, extract_pdf

SOURCES = ROOT / "data" / "manual" / "waittime_sources.csv"
INVENTORY = ROOT / "docs" / "data_inventory" / "wachttijden"
_FOLLOW = re.compile(r"wachttijd|toegangstijd", re.IGNORECASE)


def main() -> int:
    sources = pd.read_csv(SOURCES, dtype=str).dropna(subset=["wachttijden_url"])
    http = PoliteSession()
    out = raw_dir("waits")
    INVENTORY.mkdir(parents=True, exist_ok=True)
    results = {}
    for row in sources.itertuples():
        key, url = row.organisatie_agb, row.wachttijden_url
        try:
            resp = http.get(url)
            if resp.content[:4] == b"%PDF":
                text, tables = extract_pdf(resp.content)
            else:
                page = decode_html(resp)
                text, tables = extract_html(page)
                pdfs = [u for u, t in all_links(page, resp.url) if u.lower().endswith(".pdf") and _FOLLOW.search(f"{u} {t}")]
                for pdf_url in pdfs[:1]:  # the newest overview is usually the first link
                    doc = http.get(pdf_url)
                    if doc.content[:4] == b"%PDF":
                        pdf_text, pdf_tables = extract_pdf(doc.content)
                        text += f"\n\n[linked document: {pdf_url}]\n{pdf_text}"
                        tables += pdf_tables
            (out / f"{key}.tables.json").write_text(json.dumps(tables, ensure_ascii=False), encoding="utf-8")
            (out / f"{key}.txt").write_text(text, encoding="utf-8")
            (INVENTORY / f"{key}.txt").write_text(f"source: {url}\nfetched: {today()}\n\n{text}", encoding="utf-8")
            results[key] = {"url": url, "ok": True, "tables": len(tables)}
            print(f"ok   {key}: {len(tables)} tables")
        except Exception as exc:
            results[key] = {"url": url, "ok": False, "error": str(exc)[:200]}
            print(f"FAIL {key}: {exc}", file=sys.stderr)
    write_meta(out, source="waits", results=results)
    ok = sum(r["ok"] for r in results.values())
    print(f"{ok}/{len(results)} waiting-time pages fetched")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
