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
from urllib.parse import urlparse

import pandas as pd
import pdfplumber

from scrapers.common import ROOT, PoliteSession, raw_dir, today, write_meta

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


_LABELLED = re.compile(r"<[^>]*?\b(?:alt|aria-label|title)\s*=\s*[\"']([^\"']{2,80})[\"'][^>]*>", re.IGNORECASE)


def html_to_text(page: str) -> str:
    """Visible text plus the alt/aria-label/title of icons: many contract overviews show the status
    as an icon whose meaning ('Gecontracteerd', 'In onderhandeling') is only in that attribute."""
    page = _LABELLED.sub(lambda m: f" {m.group(1)} ", _DROP.sub(" ", page))
    page = _BLOCK.sub("\n", page)
    text = html_lib.unescape(re.sub(r"<[^>]+>", " ", page))
    lines = (re.sub(r"[ \t ]+", " ", line).strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)


def extract_html(page: str) -> tuple[str, list[Table]]:
    tables: list[Table] = []
    try:
        frames = pd.read_html(io.StringIO(page), flavor="lxml")
    except Exception:  # no <table>, or a table lxml cannot read: the text fallback still works
        frames = []
    for df in frames:
        body = df.astype(object).where(df.notna(), None).values.tolist()
        body = [[c if c is None else str(c) for c in row] for row in body]
        # without <th>, pandas numbers the columns 0, 1, ... and the real header stays in the body
        synthetic = all(isinstance(c, int) or str(c).startswith("Unnamed") for c in df.columns)
        header = [] if synthetic else [[" ".join(map(str, c)) if isinstance(c, tuple) else str(c) for c in df.columns]]
        tables.append(header + body)
    return html_to_text(page), tables


# links from a contract page to the actual overview ('Bekijk de status afspraken 2027', a PDF, ...)
_DOC_LINK = re.compile(r"status|overzicht|afspraken|contract|zorgverzekeraar|onderhandel", re.IGNORECASE)
_DOC_TARGET = re.compile(r"\.pdf(\?|$)|/media/|/documents?/|download", re.IGNORECASE)
MAX_FOLLOW = 3


def decode_html(resp) -> str:
    """Pages often omit the charset header; requests then assumes latin-1 ('PatiÃ«nt')."""
    try:
        return resp.content.decode("utf-8")
    except UnicodeDecodeError:
        return resp.content.decode(resp.apparent_encoding or "cp1252", errors="replace")


def linked_documents(page: str, base_url: str) -> list[str]:
    from scrapers.common import all_links
    host = urlparse(base_url).netloc.split(".", 1)[-1]
    hits = [url for url, text in all_links(page, base_url)
            if _DOC_TARGET.search(url) and _DOC_LINK.search(f"{text} {url}") and host in urlparse(url).netloc]
    return list(dict.fromkeys(hits))[:MAX_FOLLOW]


def sources() -> dict[str, str]:
    """{organisation AGB: contract page URL}. Contracts are agreed per organisation, so the AGB is the key.
    data/manual/contract_sources.csv lists the pages found nationally; a URL in hospitals.csv
    (checked by hand) wins for the same organisation."""
    manual = ROOT / "data" / "manual"
    found = pd.read_csv(manual / "contract_sources.csv", dtype=str) if (manual / "contract_sources.csv").exists() \
        else pd.DataFrame(columns=["organisatie_agb", "url"])
    urls = dict(zip(found["organisatie_agb"], found["url"]))
    hospitals = pd.read_csv(manual / "hospitals.csv", dtype=str)
    checked = hospitals[hospitals["contracts_url"].fillna("").str.startswith("http") & hospitals["agb_code"].notna()]
    urls.update(dict(zip(checked["agb_code"], checked["contracts_url"])))
    return {agb: url for agb, url in urls.items() if isinstance(url, str) and url.startswith("http")}


def main() -> int:
    targets = sources()
    if not targets:
        print("No contract sources")
        return 0
    http = PoliteSession()
    out = raw_dir("contracts")
    results, failures = {}, 0
    for key, url in targets.items():
        try:
            resp = http.get(url)
            is_pdf = "pdf" in resp.headers.get("Content-Type", "").lower() or resp.content[:4] == b"%PDF"
            if is_pdf:
                (out / f"{key}.pdf").write_bytes(resp.content)
                text, tables = extract_pdf(resp.content)
            else:
                page = decode_html(resp)
                (out / f"{key}.html").write_text(page, encoding="utf-8")
                text, tables = extract_html(page)
                for doc_url in linked_documents(page, resp.url):  # follow to the actual overview
                    try:
                        doc = http.get(doc_url)
                    except Exception as exc:
                        print(f"     {key}: could not follow {doc_url}: {exc}", file=sys.stderr)
                        continue
                    if doc.content[:4] == b"%PDF":
                        doc_text, doc_tables = extract_pdf(doc.content)
                    else:
                        doc_text, doc_tables = extract_html(decode_html(doc))
                    text += f"\n\n[linked document: {doc_url}]\n{doc_text}"
                    tables += doc_tables
                    print(f"     {key}: followed {doc_url} ({len(doc_tables)} tables)")
            (out / f"{key}.txt").write_text(text, encoding="utf-8")
            # keep the extracted text in the repo: public, small, and needed to improve the parser
            inventory = ROOT / "docs" / "data_inventory" / "contracts"
            inventory.mkdir(parents=True, exist_ok=True)
            (inventory / f"{key}.txt").write_text(f"source: {url}\n\n{text}", encoding="utf-8")
            (out / f"{key}.tables.json").write_text(json.dumps(tables, ensure_ascii=False, indent=1), encoding="utf-8")
            results[key] = {"url": url, "final_url": resp.url, "organisatie_agb": key,
                            "format": "pdf" if is_pdf else "html", "tables": len(tables), "ok": True}
            print(f"ok   {key}: {'pdf' if is_pdf else 'html'}, {len(tables)} tables")
        except Exception as exc:  # keep going for the other hospitals
            failures += 1
            results[key] = {"url": url, "organisatie_agb": key, "ok": False, "error": str(exc)}
            print(f"FAIL {key}: {exc}", file=sys.stderr)
    write_meta(out, source="contracts", results=results)
    write_fetch_report(results)
    return 1 if failures == len(targets) else 0


def write_fetch_report(results: dict) -> None:
    """docs/data_inventory/contract_fetch.md: per organisation whether its page could be fetched."""
    lines = ["# Contractpagina's ophalen", "", f"Laatste run: {today()}.", "",
             "| AGB | resultaat | URL |", "|---|---|---|"]
    for key, r in sorted(results.items(), key=lambda kv: kv[1].get("ok", False)):
        outcome = f"ok ({r.get('format')}, {r.get('tables', 0)} tabellen)" if r.get("ok") else \
            "fout: " + str(r.get("error", ""))[:120].replace("|", "/")
        lines.append(f"| {key} | {outcome} | {r.get('url')} |")
    path = ROOT / "docs" / "data_inventory" / "contract_fetch.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
