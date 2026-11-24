"""Download the Zorginzicht open data files for medisch-specialistische zorg (MSZ).

Downloads every Excel/zip/csv link on the MSZ open-data page (the page holds the
yearly files and their 'naleveringen'). A link that fails is logged and skipped.
Output: data/raw/zorginzicht/<today>/<files> + meta.json + links.json

Usage: python -m scrapers.zorginzicht
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from scrapers.common import PoliteSession, find_links, raw_dir, safe_filename, write_meta

LANDING = (
    "https://www.zorginzicht.nl/algemeen/"
    "open-data-medisch-specialistische-zorg-msz-ziekenhuizen-en-zelfstandige-behandelcentra"
)
FILE_PATTERN = r"\.(xlsx?|zip|csv)(\?|$)"
EXTENSIONS = {
    "spreadsheetml": ".xlsx", "ms-excel": ".xls", "zip": ".zip", "csv": ".csv",
}


def unique_name(directory: Path, url: str, content_disposition: str | None, content_type: str) -> str:
    name = safe_filename(url, content_disposition)
    if Path(name).suffix.lower() not in {".xlsx", ".xls", ".zip", ".csv"}:
        name += next((ext for key, ext in EXTENSIONS.items() if key in content_type.lower()), "")
    stem, suffix, n = Path(name).stem, Path(name).suffix, 1
    while (directory / name).exists():
        n += 1
        name = f"{stem}_{n}{suffix}"
    return name


def main() -> int:
    http = PoliteSession()
    page = http.get(LANDING)
    links = find_links(page.text, page.url, FILE_PATTERN)
    out = raw_dir("zorginzicht")
    (out / "links.json").write_text(json.dumps(links, indent=2), encoding="utf-8")
    if not links:
        print("No data files found on the landing page; the page layout may have changed.", file=sys.stderr)
        return 1
    downloaded, failed = [], []
    for url in links:
        try:
            resp = http.get(url)
        except Exception as exc:  # old links linger on pages; skip them
            failed.append({"url": url, "error": str(exc)})
            print(f"FAIL {url}: {exc}", file=sys.stderr)
            continue
        name = unique_name(out, url, resp.headers.get("Content-Disposition"), resp.headers.get("Content-Type", ""))
        (out / name).write_bytes(resp.content)
        downloaded.append({"file": name, "url": url})
        print(f"downloaded {name} ({len(resp.content):,} bytes)")
    write_meta(out, source="zorginzicht_msz", url=LANDING, files=downloaded, failed=failed)
    return 0 if downloaded else 1


if __name__ == "__main__":
    sys.exit(main())
