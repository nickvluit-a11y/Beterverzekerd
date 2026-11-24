"""Download the NZa dataset 'Wachttijden medisch-specialistische zorg' (CSV, updated every 2 weeks).

The landing page on puc.overheid.nl links to the current version through
DownloadDocument.ashx?identifier=PUC_651798_22&versienummer=<n>&type=csv.
Output: data/raw/nza_wachttijden/<today>/wachttijden.csv + meta.json

Usage: python -m scrapers.nza_wachttijden
"""

from __future__ import annotations

import re
import sys

from scrapers.common import PoliteSession, find_links, raw_dir, write_meta

LANDING = "https://puc.overheid.nl/nza/doc/PUC_651798_22/"
LINK_PATTERN = r"DownloadDocument\.ashx.*PUC_651798_22.*type=csv|\.csv(\?|$)"


def pick_latest(links: list[str]) -> str | None:
    """Prefer the link with the highest versienummer."""
    def version(url: str) -> int:
        match = re.search(r"versienummer=(\d+)", url)
        return int(match.group(1)) if match else -1
    return max(links, key=version) if links else None


def main() -> int:
    http = PoliteSession()
    page = http.get(LANDING)
    url = pick_latest(find_links(page.text, page.url, LINK_PATTERN))
    if not url:
        print("No CSV link found on the NZa landing page; the page layout may have changed.", file=sys.stderr)
        return 1
    resp = http.get(url)
    out = raw_dir("nza_wachttijden")
    (out / "wachttijden.csv").write_bytes(resp.content)
    peildatum = re.search(r"peildatum\s*\(?(\d{1,2} \w+ \d{4})", page.text, re.IGNORECASE)
    write_meta(out, source="nza_wachttijden", url=url, landing=LANDING,
               peildatum_text=peildatum.group(1) if peildatum else None)
    print(f"downloaded {url} ({len(resp.content):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
