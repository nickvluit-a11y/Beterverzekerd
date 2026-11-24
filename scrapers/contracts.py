"""Download the contract overviews hospitals publish (PDF or HTML page), per data/manual/hospitals.csv.

Each distinct `contracts_url` is fetched once; locations sharing it (one organisation,
several sites) are recorded together in meta.json. Output per URL, keyed by the first
location_id using it:
  data/raw/contracts/<today>/<key>.pdf|.html   original
  data/raw/contracts/<today>/<key>.txt         plain text
  data/raw/contracts/<today>/<key>.tables.json tables as lists of rows
  data/raw/contracts/<today>/meta.json

One failing hospital does not stop the others.
Usage: python -m scrapers.contracts
"""

from __future__ import annotations

import html as html_lib
import io
import json
import re
import sys

import pandas as pd
import pdfplumber

from scrapers.common import ROOT, PoliteSession, raw_dir, write_meta

Table = list[list[str | None]]


def extract_pdf(data: bytes) -> tuple[str, list[Table]]:
    texts, tables = [], []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            texts.append(page.extract_text() or "")
            tables += page.extract_tables()
    return "\n\n".join(texts), tables


_DROP = re.compile(r"<(script|style|noscript|svg|nav|footer|header)\b.*?</\1>", re.IGNORECASE | re.DOTALL)
_BLOCK = re.compile(r"<(br|/p|/li|/tr|/h\d|/div|/td|/th)\b[^>]*>", re.IGNORECASE)


def html_to_text(page: str) -> str:
    page = _BLOCK.sub("\n", _DROP.sub(" ", page))
    text = html_lib.unescape(re.sub(r"<[^>]+>", " ", page))
    lines = (re.sub(r"[ \t ]+", " ", line).strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)


def extract_html(page: str) -> tuple[str, list[Table]]:
    tables: list[Table] = []
    try:
        for df in pd.read_html(io.StringIO(page)):
            header = [str(c) for c in df.columns]
            tables.append([header] + df.astype(str).where(df.notna(), None).values.tolist())
    except ValueError:  # no <table> on the page
        pass
    return html_to_text(page), tables


def main() -> int:
    table = pd.read_csv(ROOT / "data" / "manual" / "hospitals.csv")
    table = table[table["contracts_url"].fillna("").str.startswith("http")]
    if table.empty:
        print("No contracts_url filled in hospitals.csv")
        return 0
    groups = table.groupby("contracts_url", sort=False)["location_id"].apply(list)
    http = PoliteSession()
    out = raw_dir("contracts")
    results, failures = {}, 0
    for url, location_ids in groups.items():
        key = location_ids[0]
        try:
            resp = http.get(url)
            is_pdf = "pdf" in resp.headers.get("Content-Type", "").lower() or resp.content[:4] == b"%PDF"
            if is_pdf:
                (out / f"{key}.pdf").write_bytes(resp.content)
                text, tables = extract_pdf(resp.content)
            else:
                (out / f"{key}.html").write_text(resp.text, encoding="utf-8")
                text, tables = extract_html(resp.text)
            (out / f"{key}.txt").write_text(text, encoding="utf-8")
            (out / f"{key}.tables.json").write_text(json.dumps(tables, ensure_ascii=False, indent=1), encoding="utf-8")
            results[key] = {"url": url, "final_url": resp.url, "location_ids": location_ids,
                            "format": "pdf" if is_pdf else "html", "tables": len(tables), "ok": True}
            print(f"ok   {key} ({', '.join(location_ids)}): {'pdf' if is_pdf else 'html'}, {len(tables)} tables")
        except Exception as exc:  # keep going for the other hospitals
            failures += 1
            results[key] = {"url": url, "location_ids": location_ids, "ok": False, "error": str(exc)}
            print(f"FAIL {key}: {exc}", file=sys.stderr)
    write_meta(out, source="contracts", results=results)
    return 1 if failures == len(groups) else 0


if __name__ == "__main__":
    sys.exit(main())
