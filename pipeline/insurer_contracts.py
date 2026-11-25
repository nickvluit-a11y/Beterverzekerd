"""Link contract statuses from insurers' own care finders to hospital organisations.

A finder lists locations by name and street address. We match a finder entry to our locations on
town + house number (name similarity breaks ties), else on a clearly similar name in the same
town. Contracts are kept per organisation AGB (that is how contracts are made); when locations of
one organisation get different statuses, the least favourable one is kept, so we never promise
more than the insurer does.

Input:  data/processed/cz_zorgvinder.csv (scrapers/cz_zorgvinder.py), data/reference/locations.csv
Output: data/processed/contracts_insurer.csv, docs/data_inventory/contracts_insurer.md
Usage: python -m pipeline.insurer_contracts
"""

from __future__ import annotations

import difflib
import re
import sys

import pandas as pd

from pipeline.reference import PROCESSED, REFERENCE, ROOT, normalise

FINDERS = ["cz_zorgvinder"]
WORST_FIRST = ["geen_contract", "in_onderhandeling", "vergoed_als_contract", "gecontracteerd"]
MIN_NAME_SIMILARITY = 0.75
MIN_SIMILARITY_SAME_ADDRESS = 0.5
COLUMNS = ["year", "organisatie_agb", "concern", "label", "status", "omzetplafond", "peildatum", "source",
           "source_url", "fetched_on", "matched_locations"]


def _number(value: object) -> str:
    match = re.search(r"\b(\d+)", str(value)) if isinstance(value, str) else None
    if match is None and value is not None and not pd.isna(value):
        match = re.search(r"(\d+)", str(value))
    return match.group(1) if match else ""


_GENERIC = {"ziekenhuis", "ziekenhuizen", "locatie", "loc", "stichting", "bv", "b", "v", "mc", "medisch", "centrum",
            "polikliniek", "kliniek", "clinics", "clinic", "st", "sint", "de", "het", "van", "en", "voor", "the",
            "zkh", "zh", "nederland", "concern", "groep"}


def _tokens(text: object, city: str = "") -> set[str]:
    words = set(re.findall(r"[a-z0-9]+", normalise(text)))
    return {w for w in words if len(w) > 1 and w not in _GENERIC and w not in set(city.split())}


def _similarity(a: object, b: object, city: str = "") -> float:
    """Share of the distinctive words of the shorter name found in the other ('St. Antonius
    Ziekenhuis Locatie Utrecht' vs 'Sint Antonius Ziekenhuis' -> 1.0; vs 'Diakonessenhuis' -> 0)."""
    ta, tb = _tokens(a, city), _tokens(b, city)
    if not ta or not tb:
        return 0.5 * difflib.SequenceMatcher(None, normalise(a), normalise(b)).ratio()
    return len(ta & tb) / min(len(ta), len(tb))


def match_entries(entries: pd.DataFrame, locations: pd.DataFrame) -> pd.DataFrame:
    """entries + location_key / organisatie_agb of the matching location (None when no match).

    A pair counts when the names look alike: a little with the same town + house number, clearly
    without. Each location keeps only its best-matching entry, so a clinic of another hospital in
    the same building does not overwrite the location's own status."""
    locs = locations.assign(city=locations["plaats"].fillna("").str.lower().str.strip(),
                            number=locations["huisnummer"].map(_number),
                            name=locations["locatie_naam"].fillna(locations["organisatie_naam"]))
    pairs = []
    for idx, e in zip(entries.index, entries.itertuples()):
        number = _number(e.address)
        for loc in locs[locs["city"] == str(e.city).lower().strip()].itertuples():
            city = str(e.city).lower().strip()
            sim = max(_similarity(loc.name, e.name, city), _similarity(loc.organisatie_naam, e.name, city))
            same_address = bool(number) and loc.number == number
            if sim >= (MIN_SIMILARITY_SAME_ADDRESS if same_address else MIN_NAME_SIMILARITY):
                pairs.append((sim + (0.5 if same_address else 0), idx, loc.location_key, loc.organisatie_agb))
    keys, agbs, used_entries, used_locs = {}, {}, set(), set()
    for score, idx, key, agb in sorted(pairs, key=lambda p: -p[0]):
        if idx in used_entries or key in used_locs:
            continue
        used_entries.add(idx), used_locs.add(key)
        keys[idx], agbs[idx] = key, agb
    return entries.assign(location_key=pd.Series(keys, dtype=object), organisatie_agb=pd.Series(agbs, dtype=object))


def valid_agb(agb: object) -> bool:
    """A real organisation AGB code: 8 digits, not a placeholder like 00000000 (which in the
    Zorginzicht data is shared by unrelated clinics)."""
    text = str(agb).zfill(8) if isinstance(agb, str) and agb.strip() else ""
    return text.isdigit() and len(text) == 8 and int(text) != 0


def per_organisation(matched: pd.DataFrame) -> pd.DataFrame:
    """One row per organisation; for a placeholder AGB one row per location (key = location_key)."""
    rows = []
    matched = matched.dropna(subset=["organisatie_agb"]).copy()
    matched["organisatie_agb"] = [a if valid_agb(a) else k for a, k in zip(matched["organisatie_agb"], matched["location_key"])]
    for (agb, concern, label), g in matched.groupby(["organisatie_agb", "concern", "label"]):
        status = min(g["status"], key=lambda s: WORST_FIRST.index(s) if s in WORST_FIRST else 0)
        rows.append({"year": int(g["year"].iloc[0]), "organisatie_agb": str(agb).zfill(8) if valid_agb(agb) else agb,
                     "concern": concern,
                     "label": label, "status": status,
                     "omzetplafond": bool(g["omzetplafond"].astype(str).str.lower().eq("true").any()),
                     "peildatum": g["fetched_on"].max(), "source": g["source"].iloc[0],
                     "source_url": g["source_url"].iloc[0], "fetched_on": g["fetched_on"].max(),
                     "matched_locations": "; ".join(sorted(set(g["name"])))})
    return pd.DataFrame(rows, columns=COLUMNS)


def main() -> int:
    locations = pd.read_csv(REFERENCE / "locations.csv", dtype=str)
    frames, lines = [], ["# Contracten uit zorgzoekers van verzekeraars", ""]
    for finder in FINDERS:
        path = PROCESSED / f"{finder}.csv"
        if not path.exists():
            lines.append(f"- {finder}: nog geen data")
            continue
        entries = pd.read_csv(path, dtype=str)
        matched = match_entries(entries, locations)
        orgs = per_organisation(matched)
        frames.append(orgs)
        lines += [f"## {finder}", "",
                  f"{len(entries)} locaties in de zorgzoeker, {matched['location_key'].notna().sum()} gekoppeld aan "
                  f"onze locaties, {len(orgs)} organisaties met een status.", "",
                  "Status per organisatie: " + ", ".join(f"{k} {v}" for k, v in orgs["status"].value_counts().items()), "",
                  "Niet gekoppeld (eerste 40):", ""]
        lines += [f"- {r.name}, {r.address}, {r.city} ({r.status})"
                  for r in matched[matched["location_key"].isna()].head(40).itertuples()]
        lines.append("")
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=COLUMNS)
    out.to_csv(PROCESSED / "contracts_insurer.csv", index=False)
    report = ROOT / "docs" / "data_inventory" / "contracts_insurer.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"contracts_insurer.csv: {len(out)} organisation x insurer rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
