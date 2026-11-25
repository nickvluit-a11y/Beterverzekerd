"""Link ZorgkaartNederland ratings to our hospital locations.

Order: same postcode (and, if several locations share it, the most similar name); otherwise the
most similar name in the same city. Only the average score and the count are kept.

Input:  data/processed/reviews.csv (scrapers/zorgkaart.py), data/reference/locations.csv
Output: data/processed/reviews_linked.csv (location_key, rating, count, zkn_url, fetched_on)
Usage: python -m pipeline.reviews_ingest
"""

from __future__ import annotations

import difflib
import sys

import pandas as pd

from pipeline.reference import PROCESSED, REFERENCE, normalise

MIN_NAME_SIMILARITY = 0.6


def _similarity(a: object, b: object) -> float:
    return difflib.SequenceMatcher(None, normalise(a), normalise(b)).ratio()


def link(reviews: pd.DataFrame, locations: pd.DataFrame) -> pd.DataFrame:
    locations = locations.assign(name=locations["locatie_naam"].fillna(locations["organisatie_naam"]),
                                 city=locations["plaats"].fillna("").str.lower())
    rows = []
    for r in reviews.itertuples():
        candidates = locations[locations["postcode"] == r.postcode] if isinstance(r.postcode, str) else locations.iloc[0:0]
        if candidates.empty and isinstance(r.city, str):
            candidates = locations[locations["city"] == r.city.lower()]
        if candidates.empty:
            continue
        scores = candidates["name"].map(lambda n: _similarity(n, r.name))
        best = scores.idxmax()
        same_postcode = isinstance(r.postcode, str) and candidates.loc[best, "postcode"] == r.postcode
        if same_postcode and len(candidates) == 1 or scores[best] >= MIN_NAME_SIMILARITY:
            rows.append({"location_key": candidates.loc[best, "location_key"], "rating": r.rating, "count": r.count,
                         "zkn_name": r.name, "zkn_url": r.zkn_url, "fetched_on": r.fetched_on})
    linked = pd.DataFrame(rows, columns=["location_key", "rating", "count", "zkn_name", "zkn_url", "fetched_on"])
    # one rating per location: the page with the most ratings
    return linked.sort_values("count", ascending=False).drop_duplicates("location_key").reset_index(drop=True)


def main() -> int:
    reviews_path, locations_path = PROCESSED / "reviews.csv", REFERENCE / "locations.csv"
    if not reviews_path.exists() or not locations_path.exists():
        print("No reviews or locations yet", file=sys.stderr)
        return 1
    reviews = pd.read_csv(reviews_path, dtype={"postcode": str})
    linked = link(reviews, pd.read_csv(locations_path, dtype=str))
    linked.to_csv(PROCESSED / "reviews_linked.csv", index=False)
    print(f"reviews linked: {len(linked)} locations (of {len(reviews)} rating pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
