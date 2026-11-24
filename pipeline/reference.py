"""Load the hand-maintained reference tables and match free-text names to them."""

from __future__ import annotations

import difflib
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MANUAL = ROOT / "data" / "manual"
PROCESSED = ROOT / "data" / "processed"

# Words that carry no meaning for matching hospital names
_STOPWORDS = {"ziekenhuis", "ziekenhuizen", "medisch", "centrum", "mc", "stichting", "locatie", "de", "het", "st", "sint"}


def normalise(text: str) -> str:
    """Lowercase, strip accents and punctuation, drop stopwords."""
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    words = re.sub(r"[^a-z0-9 ]+", " ", text.lower()).split()
    return " ".join(w for w in words if w not in _STOPWORDS)


@lru_cache
def hospitals() -> pd.DataFrame:
    return pd.read_csv(MANUAL / "hospitals.csv", dtype={"agb_code": str, "postcode": str})


@lru_cache
def labels() -> pd.DataFrame:
    return pd.read_csv(MANUAL / "concerns_labels.csv")


@lru_cache
def procedures() -> pd.DataFrame:
    return pd.read_csv(MANUAL / "procedures.csv")


def _alias_index() -> list[tuple[str, str]]:
    """(normalised alias, location_id) pairs for every name a location is known by."""
    pairs = []
    for row in hospitals().itertuples():
        names = [row.organisation, row.location_name] + str(row.aliases or "").split("|")
        pairs += [(normalise(n), row.location_id) for n in names if isinstance(n, str) and n.strip()]
    return pairs


def match_location(name: str, city: str | None = None, agb_code: str | None = None, cutoff: float = 0.85) -> str | None:
    """Return the location_id for a hospital name as written in some source, or None.

    Order: exact AGB code, exact alias, fuzzy alias. When a name matches several
    locations of the same organisation, `city` decides; without a city, an
    organisation-level name maps to its first listed location only if it has one location.
    """
    table = hospitals()
    if agb_code:
        hit = table[table["agb_code"].fillna("") == str(agb_code).strip()]
        if len(hit) == 1:
            return hit.iloc[0]["location_id"]
    target = normalise(name)
    if not target:
        return None
    index = _alias_index()
    candidates = {loc for alias, loc in index if alias == target}
    if not candidates:
        best = difflib.get_close_matches(target, [a for a, _ in index], n=3, cutoff=cutoff)
        candidates = {loc for alias, loc in index if alias in best}
    if len(candidates) > 1 and city:
        in_city = set(table[table["city"].str.lower() == city.strip().lower()]["location_id"])
        candidates &= in_city
    return candidates.pop() if len(candidates) == 1 else None


def match_label(text: str) -> tuple[str, str | None] | None:
    """Map free text to (concern, label). A bare concern name gives (concern, None)."""
    target = normalise(text)
    if not target:
        return None
    table = labels()
    for row in table.itertuples():
        if normalise(row.label) == target:
            return row.concern, row.label
    for concern in table["concern"].unique():
        if normalise(concern) == target:
            return concern, None
    return None
