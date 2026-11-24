"""Download the NZa dataset 'Wachttijden medisch-specialistische zorg' (CSV, updated every 2 weeks).

The landing page on puc.overheid.nl links to its files through
DownloadDocument.ashx?identifier=PUC_<n>&versienummer=<v> links whose identifiers change with
every update. We try the links (CSV-looking text first, newest identifier first) and keep the
first response that is a CSV with a waiting-time header.
Output: data/raw/nza_wachttijden/<today>/wachttijden.csv + meta.json
        docs/data_inventory/nza_wachttijden_links.md (all links on the page)

Usage: python -m scrapers.nza_wachttijden
"""

from __future__ import annotations

import re
import sys

from scrapers.common import PoliteSession, all_links, raw_dir, write_link_inventory, write_meta

LANDING = "https://puc.overheid.nl/nza/doc/PUC_651798_22/"
LINK_PATTERN = re.compile(r"DownloadDocument\.ashx|\.csv(\?|$)", re.IGNORECASE)
MAX_TRIES = 10


def candidate_order(links: list[tuple[str, str]]) -> list[str]:
    """Download links, CSV/dataset-looking text first, then the highest PUC identifier first."""
    def key(item: tuple[str, str]) -> tuple[int, int]:
        url, text = item
        textual = 0 if re.search(r"csv|dataset|wachttijden", f"{text} {url}", re.IGNORECASE) else 1
        ident = re.search(r"PUC_(\d+)", url)
        return textual, -(int(ident.group(1)) if ident else 0)
    hits = [(u, t) for u, t in links if LINK_PATTERN.search(u)]
    return list(dict.fromkeys(u for u, _ in sorted(hits, key=key)))


def is_waiting_time_csv(content: bytes) -> bool:
    head = content[:2000].decode("utf-8", errors="ignore").lower()
    first = head.splitlines()[0] if head else ""
    return "wacht" in first and (first.count(";") >= 3 or first.count(",") >= 3)


def main() -> int:
    http = PoliteSession()
    page = http.get(LANDING)
    links = all_links(page.text, page.url)
    write_link_inventory("nza_wachttijden", page.url, links)
    tried = []
    for url in candidate_order(links)[:MAX_TRIES]:
        try:
            resp = http.get(url)
        except Exception as exc:
            tried.append({"url": url, "error": str(exc)})
            continue
        tried.append({"url": url, "content_type": resp.headers.get("Content-Type", ""), "bytes": len(resp.content)})
        if is_waiting_time_csv(resp.content):
            out = raw_dir("nza_wachttijden")
            (out / "wachttijden.csv").write_bytes(resp.content)
            peildatum = re.search(r"peildatum\s*\(?(\d{1,2} \w+ \d{4})", page.text, re.IGNORECASE)
            write_meta(out, source="nza_wachttijden", url=url, landing=LANDING, tried=tried,
                       peildatum_text=peildatum.group(1) if peildatum else None)
            print(f"downloaded {url} ({len(resp.content):,} bytes)")
            return 0
    print(f"No waiting-time CSV among {len(tried)} tried links: {tried}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
