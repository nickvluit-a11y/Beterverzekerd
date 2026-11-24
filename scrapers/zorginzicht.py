"""Download the Zorginzicht open data files for medisch-specialistische zorg (MSZ).

Finds every Excel/zip link on the MSZ open-data page and downloads the ones whose
link text or URL mention 'msz' / 'openbaar databestand'. Output:
data/raw/zorginzicht/<today>/<files> + meta.json + links.json

Usage: python -m scrapers.zorginzicht
"""

from __future__ import annotations

import json
import sys

from scrapers.common import PoliteSession, find_links, raw_dir, safe_filename, write_meta

LANDING = (
    "https://www.zorginzicht.nl/algemeen/"
    "open-data-medisch-specialistische-zorg-msz-ziekenhuizen-en-zelfstandige-behandelcentra"
)
FILE_PATTERN = r"\.(xlsx?|zip|csv)(\?|$)"


def main() -> int:
    http = PoliteSession()
    page = http.get(LANDING)
    links = find_links(page.text, page.url, FILE_PATTERN)
    out = raw_dir("zorginzicht")
    (out / "links.json").write_text(json.dumps(links, indent=2), encoding="utf-8")
    if not links:
        print("No data files found on the landing page; the page layout may have changed.", file=sys.stderr)
        return 1
    downloaded = []
    for url in links:
        resp = http.get(url)
        name = safe_filename(url, resp.headers.get("Content-Disposition"))
        (out / name).write_bytes(resp.content)
        downloaded.append(name)
        print(f"downloaded {name} ({len(resp.content):,} bytes)")
    write_meta(out, source="zorginzicht_msz", url=LANDING, files=downloaded)
    return 0


if __name__ == "__main__":
    sys.exit(main())
