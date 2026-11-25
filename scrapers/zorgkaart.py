"""Patient ratings per hospital location from ZorgkaartNederland: ONLY the average score and the
number of ratings (no review texts, no names of care providers), see CLAUDE.md.

robots.txt allows general crawlers (only AI-training bots are excluded; we train nothing). Each
hospital page carries a schema.org AggregateRating in JSON-LD, which is read as is.

Output: data/processed/reviews.csv (+ dated history): zkn_url, name, postcode, city, rating, count.
Linking to our locations happens in pipeline/reviews_ingest.py.
Usage: python -m scrapers.zorgkaart [max_pages]
"""

from __future__ import annotations

import json
import re
import sys

import pandas as pd

from pipeline.reference import save_with_history
from scrapers.common import PoliteSession, find_links, today

BASE = "https://www.zorgkaartnederland.nl"
LISTING = BASE + "/ziekenhuis/pagina{page}"
_INSTITUTION = re.compile(r"/zorginstelling/ziekenhuis-[a-z0-9-]+-\d+/?$")
_LD = re.compile(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', re.S | re.I)


def parse_institution(html: str, url: str) -> dict | None:
    """Name, address and aggregate rating from the JSON-LD of a hospital page."""
    for block in _LD.findall(html):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        for item in data if isinstance(data, list) else [data]:
            if not isinstance(item, dict) or "aggregateRating" not in item:
                continue
            rating, address = item["aggregateRating"], item.get("address") or {}
            if isinstance(address, list):
                address = address[0] if address else {}
            return {"zkn_url": url, "name": item.get("name"),
                    "postcode": str(address.get("postalCode", "")).replace(" ", "").upper() or None,
                    "city": address.get("addressLocality"),
                    "rating": rating.get("ratingValue"), "count": rating.get("ratingCount")}
    return None


def main(argv: list[str]) -> int:
    max_pages = int(argv[0]) if argv else 60
    http = PoliteSession(delay=3)
    urls: list[str] = []
    for page in range(1, max_pages + 1):
        listing_url = BASE + "/ziekenhuis" if page == 1 else LISTING.format(page=page)
        try:
            resp = http.get(listing_url)
        except Exception as exc:
            print(f"stop at listing page {page}: {exc}", file=sys.stderr)
            break
        found = [u.rstrip("/") for u in find_links(resp.text, resp.url, r"/zorginstelling/ziekenhuis-") if _INSTITUTION.search(u)]
        new = [u for u in dict.fromkeys(found) if u not in urls]
        if not new:
            break
        urls += new
        print(f"listing page {page}: {len(new)} hospitals")
    rows = []
    for url in urls:
        try:
            row = parse_institution(http.get(url).text, url)
        except Exception as exc:
            print(f"FAIL {url}: {exc}", file=sys.stderr)
            continue
        if row:
            rows.append(row)
    if not rows:
        print("No ratings found", file=sys.stderr)
        return 1
    df = pd.DataFrame(rows).assign(source="ZorgkaartNederland", fetched_on=today())
    save_with_history(df, "reviews", today())
    print(f"reviews.csv: {len(df)} hospital pages with a rating")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
