"""Add coordinates to every location via the PDOK Locatieserver (government address register).

Input:  data/reference/locations_zorginzicht.csv
Cache:  data/reference/geocode_cache.csv  (postcode, huisnummer -> lat, lon, precision); committed,
        so each address is looked up once
Output: data/reference/locations.csv      (locations + lat/lon)

Address lookup first (postcode + house number); postcode centroid as fallback.
Usage: python -m pipeline.geocode
"""

from __future__ import annotations

import re
import sys

import pandas as pd

from pipeline.geo import PDOK_URL, parse_point
from pipeline.reference import ROOT

REFERENCE = ROOT / "data" / "reference"
CACHE = REFERENCE / "geocode_cache.csv"
CACHE_COLUMNS = ["postcode", "huisnummer", "lat", "lon", "precision"]


def house_number(value: object) -> str:
    match = re.match(r"\s*(\d+)", str(value)) if value is not None and not pd.isna(value) else None
    return match.group(1) if match else ""


def lookup(http, postcode: str, number: str) -> tuple[float, float, str] | None:
    queries = []
    if number:
        queries.append(({"q": f"postcode:{postcode} AND huisnummer:{number}", "fq": "type:adres"}, "adres"))
    queries.append(({"q": f"postcode:{postcode}", "fq": "type:postcode"}, "postcode"))
    for params, precision in queries:
        resp = http.get(PDOK_URL, params={**params, "rows": 1, "fl": "centroide_ll"})
        docs = resp.json().get("response", {}).get("docs", [])
        point = parse_point(docs[0]["centroide_ll"]) if docs else None
        if point:
            return point[0], point[1], precision
    return None


def main() -> int:
    from scrapers.common import PoliteSession  # network only here, keeps tests import-light

    locations = pd.read_csv(REFERENCE / "locations_zorginzicht.csv", dtype=str)
    locations["huisnummer_clean"] = locations["huisnummer"].map(house_number)
    cache = pd.read_csv(CACHE, dtype=str) if CACHE.exists() else pd.DataFrame(columns=CACHE_COLUMNS)
    cache["huisnummer"] = cache["huisnummer"].fillna("")
    known = set(zip(cache["postcode"], cache["huisnummer"]))
    todo = (locations.dropna(subset=["postcode"])[["postcode", "huisnummer_clean"]]
            .drop_duplicates().itertuples(index=False))
    http = PoliteSession(delay=0.3)
    new_rows, failed = [], 0
    for pc, number in todo:
        if (pc, number) in known:
            continue
        try:
            hit = lookup(http, pc, number)
        except Exception as exc:
            failed += 1
            print(f"FAIL {pc} {number}: {exc}", file=sys.stderr)
            continue
        if hit:
            new_rows.append({"postcode": pc, "huisnummer": number, "lat": hit[0], "lon": hit[1], "precision": hit[2]})
    if new_rows:
        cache = pd.concat([cache, pd.DataFrame(new_rows)], ignore_index=True)
        cache.to_csv(CACHE, index=False)
    merged = locations.merge(cache, left_on=["postcode", "huisnummer_clean"], right_on=["postcode", "huisnummer"],
                             how="left", suffixes=("", "_cache")).drop(columns=["huisnummer_cache", "huisnummer_clean"])
    merged.to_csv(REFERENCE / "locations.csv", index=False)
    print(f"geocoded {merged['lat'].notna().sum()}/{len(merged)} locations ({len(new_rows)} new lookups, {failed} failed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
