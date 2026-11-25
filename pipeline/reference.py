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
REFERENCE = ROOT / "data" / "reference"

# Words that carry no meaning for matching hospital names
_STOPWORDS = {"ziekenhuis", "ziekenhuizen", "medisch", "centrum", "mc", "stichting", "locatie", "de", "het", "st", "sint"}


def normalise(text: object) -> str:
    """Lowercase, strip accents and punctuation, drop stopwords. Non-strings give ''."""
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    words = re.sub(r"[^a-z0-9 ]+", " ", text.lower()).split()
    return " ".join(w for w in words if w not in _STOPWORDS)


def _split_aliases(value: object) -> list[str]:
    return [a for a in value.split("|") if a.strip()] if isinstance(value, str) else []


@lru_cache
def hospitals() -> pd.DataFrame:
    return pd.read_csv(MANUAL / "hospitals.csv", dtype={"agb_code": str, "postcode": str})


@lru_cache
def locations() -> pd.DataFrame:
    """All MSZ locations from Zorginzicht with coordinates (empty until the pipeline has run)."""
    path = REFERENCE / "locations.csv"
    if not path.exists():
        return pd.DataFrame(columns=["location_key", "organisatie_agb", "organisatie_naam", "locatie_naam",
                                     "postcode", "plaats", "lat", "lon"])
    return pd.read_csv(path, dtype={"organisatie_agb": str, "locatie_agb": str, "kvk": str, "postcode": str})


@lru_cache
def indicator_catalogue() -> pd.DataFrame:
    path = REFERENCE / "indicators.csv"
    return pd.read_csv(path, dtype=str) if path.exists() else pd.DataFrame(
        columns=["indicator_code", "indicator_naam", "thema", "eenheid", "indicator_type", "procedure_id"])


@lru_cache
def labels() -> pd.DataFrame:
    return pd.read_csv(MANUAL / "concerns_labels.csv")


@lru_cache
def procedures() -> pd.DataFrame:
    return pd.read_csv(MANUAL / "procedures.csv")


@lru_cache
def _alias_index() -> tuple[tuple[str, str], ...]:
    """(normalised alias, location_id) pairs for every name a location is known by."""
    pairs = []
    for row in hospitals().itertuples():
        names = [row.organisation, row.location_name] + _split_aliases(row.aliases)
        pairs += [(normalise(n), row.location_id) for n in names if normalise(n)]
    return tuple(pairs)


def match_location(name: object, city: str | None = None, agb_code: str | None = None, cutoff: float = 0.85) -> str | None:
    """Return the location_id for a hospital name as written in some source, or None.

    Order: AGB code (only if it identifies one location), exact alias, fuzzy alias.
    When a name fits several locations of one organisation, `city` decides.
    """
    table = hospitals()
    if isinstance(agb_code, str) and agb_code.strip():
        hit = table[table["agb_code"].fillna("") == agb_code.strip()]
        if len(hit) == 1:
            return hit.iloc[0]["location_id"]
        if len(hit) > 1 and isinstance(city, str):
            hit = hit[hit["city"].str.lower() == city.strip().lower()]
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
    if len(candidates) > 1 and isinstance(city, str):
        in_city = set(table[table["city"].str.lower() == city.strip().lower()]["location_id"])
        candidates &= in_city
    return candidates.pop() if len(candidates) == 1 else None


def match_label(text: object) -> tuple[str, str | None] | None:
    """Map free text to (concern, label). A bare concern name gives (concern, None)."""
    target = normalise(text)
    if not target:
        return None
    table = labels()
    for row in table.itertuples():
        names = [row.label] + _split_aliases(getattr(row, "aliases", None))
        if any(normalise(n) == target for n in names):
            return row.concern, row.label
    for concern in table["concern"].unique():
        if normalise(concern) == target:
            return concern, None
    return None


@lru_cache
def _label_names() -> tuple[tuple[str, str, str | None], ...]:
    """(normalised name, concern, label) for every label, alias and concern name; longest first."""
    names = []
    for row in labels().itertuples():
        for name in [row.label] + _split_aliases(getattr(row, "aliases", None)):
            names.append((normalise(name), row.concern, row.label))
    for concern in labels()["concern"].unique():
        names.append((normalise(concern), concern, None))
    return tuple(sorted({n for n in names if n[0]}, key=lambda n: -len(n[0])))


def find_labels(text: object) -> list[tuple[str, str | None]]:
    """All insurer labels mentioned in a short text, as (concern, label), in order of appearance.
    Longer names win over names they contain ('Zilveren Kruis' over a shorter alias)."""
    target = f" {normalise(text)} "
    taken = [False] * len(target)
    hits = []
    for name, concern, label in _label_names():
        for match in re.finditer(rf"(?<= ){re.escape(name)}(?= )", target):
            if not any(taken[match.start():match.end()]):
                taken[match.start():match.end()] = [True] * (match.end() - match.start())
                hits.append((match.start(), concern, label))
    return [(c, l) for _, c, l in sorted(hits)]


def save_with_history(df: pd.DataFrame, name: str, peildatum: str) -> Path:
    """Write data/processed/<name>.csv (latest) and data/processed/history/<name>/<peildatum>.csv."""
    PROCESSED.mkdir(parents=True, exist_ok=True)
    latest = PROCESSED / f"{name}.csv"
    df.to_csv(latest, index=False)
    history = PROCESSED / "history" / name
    history.mkdir(parents=True, exist_ok=True)
    previous = sorted(history.glob("*.csv"))
    content = latest.read_bytes()
    if not previous or previous[-1].read_bytes() != content:  # keep a snapshot only when the data changed
        (history / f"{peildatum}.csv").write_bytes(content)
    return latest
