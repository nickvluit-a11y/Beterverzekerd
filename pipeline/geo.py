"""Postcode -> coordinates via the PDOK Locatieserver (free, no key)."""

from __future__ import annotations

import re

import requests

PDOK_URL = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free"
_POSTCODE = re.compile(r"^\s*(\d{4})\s*([a-zA-Z]{2})?\s*$")
_POINT = re.compile(r"POINT\(([-\d.]+) ([-\d.]+)\)")


def clean_postcode(text: str) -> str | None:
    """'3584 cx' -> '3584CX'; '3584' -> '3584'; invalid -> None."""
    match = _POSTCODE.match(text or "")
    if not match:
        return None
    return match.group(1) + (match.group(2) or "").upper()


def parse_point(wkt: str) -> tuple[float, float] | None:
    """'POINT(5.17 52.08)' -> (lat, lon)."""
    match = _POINT.search(wkt or "")
    return (float(match.group(2)), float(match.group(1))) if match else None


def geocode_postcode(postcode: str, timeout: float = 10) -> tuple[float, float] | None:
    """(lat, lon) of a Dutch postcode (4 digits, optionally + 2 letters), or None."""
    code = clean_postcode(postcode)
    if not code:
        return None
    query = {"q": f"postcode:{code}", "fq": "type:postcode", "rows": 1, "fl": "centroide_ll"}
    if len(code) == 4:  # PC4: take the first full postcode in that area
        query = {"q": code, "fq": "type:postcode", "rows": 1, "fl": "centroide_ll"}
    resp = requests.get(PDOK_URL, params=query, timeout=timeout)
    resp.raise_for_status()
    docs = resp.json().get("response", {}).get("docs", [])
    return parse_point(docs[0]["centroide_ll"]) if docs else None


def approximate_from_cache(postcode: str, cache_path=None) -> tuple[float, float] | None:
    """Fallback when PDOK is unreachable: the mean position of known (hospital) postcodes in the same
    PC4 area, else in the nearest PC4 number within 20 (Dutch PC4 numbers are roughly geographic)."""
    import pandas as pd
    from pipeline.reference import REFERENCE
    code = clean_postcode(postcode)
    path = cache_path or REFERENCE / "geocode_cache.csv"
    if not code:
        return None
    try:
        cache = pd.read_csv(path, dtype={"postcode": str}).dropna(subset=["lat", "lon"])
    except (OSError, ValueError):
        return None
    pc4 = pd.to_numeric(cache["postcode"].str[:4], errors="coerce")
    gap = (pc4 - int(code[:4])).abs()
    if gap.empty or gap.min() > 20:
        return None
    near = cache[gap == gap.min()]
    return float(near["lat"].mean()), float(near["lon"].mean())


def locate(postcode: str) -> tuple[float, float] | None:
    """PDOK first; on a network error the approximation from the cache, so search keeps working."""
    try:
        return geocode_postcode(postcode)
    except requests.RequestException:
        return approximate_from_cache(postcode)
