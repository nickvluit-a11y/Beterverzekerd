"""Contract status 2027 per hospital location from CZ's own care finder (zorgvinder.cz.nl).

The insurer itself publishes, per location, whether it has a contract, whether a revenue cap
applies, and whether care is reimbursed as if contracted while talks continue. The pages are
server-rendered; robots.txt is respected by PoliteSession. We query hospitals around a fixed list
of towns that covers the country (25 km radius) and keep only name, address, status and cap.

Output: data/processed/cz_zorgvinder.csv (+ dated history), docs/data_inventory/cz_zorgvinder.md
Linking to hospital organisations: pipeline/insurer_contracts.py
Usage: python -m scrapers.cz_zorgvinder [max_towns]
"""

from __future__ import annotations

import re
import sys

import pandas as pd

from pipeline.reference import ROOT, save_with_history
from scrapers.common import PoliteSession, find_links, today
from scrapers.contracts import html_to_text

YEAR = 2027
URL = ("https://zorgvinder.cz.nl/resultaten/{category}/{town}?afstand=25&jaar={year}"
       "&vergoedbv=ja%2Cinclafsp%2Cnogniet%2Cnee")
# 'ziekenhuis' is known to work; the others are tried once (first town) and kept only if they list results
CATEGORIES = ["ziekenhuis", "zelfstandig-behandelcentrum", "zelfstandige-behandelcentra", "kliniek",
              "particuliere-kliniek"]
# towns spread over the country; with a 25 km radius together they cover every hospital
TOWNS = ["utrecht", "amsterdam", "rotterdam", "den-haag", "leiden", "haarlem", "alkmaar", "hoorn", "den-helder",
         "almere", "lelystad", "amersfoort", "hilversum", "gouda", "dordrecht", "gorinchem", "breda", "tilburg",
         "eindhoven", "helmond", "oss", "nijmegen", "arnhem", "ede", "apeldoorn", "zutphen", "doetinchem",
         "winterswijk", "deventer", "zwolle", "harderwijk", "meppel", "hardenberg", "almelo", "enschede",
         "assen", "emmen", "groningen", "stadskanaal", "delfzijl", "leeuwarden", "sneek", "heerenveen", "drachten",
         "goes", "middelburg", "terneuzen", "bergen-op-zoom", "roosendaal", "venlo", "weert", "roermond",
         "sittard", "heerlen", "maastricht", "tiel", "boxmeer", "uden", "dokkum", "emmeloord"]

STATUSES = {  # CZ's wording -> our status
    "contract: vergoed": "gecontracteerd",
    "(nog) geen contract: wel vergoed": "vergoed_als_contract",
    "nog geen contract: een deel niet vergoed": "in_onderhandeling",
    "geen contract: een deel niet vergoed": "geen_contract",
}
_DISTANCE = re.compile(r"^[\d,]+ km - [\d,]+ kilometer van je locatie (?P<city>[^,]+), (?P<address>.+)$")
_COUNT = re.compile(r"^(\d+) zorgverleners?$")


def parse_results(text: str) -> tuple[list[dict], int | None]:
    """Entries (name, address, city, status, omzetplafond) from the visible text of a result page,
    plus the number of results the page says it has."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    total = next((int(m.group(1)) for l in lines if (m := _COUNT.match(l))), None)
    entries: list[dict] = []
    for i, line in enumerate(lines):
        match = _DISTANCE.match(line)
        if not match or i == 0:
            continue
        address, title = match.group("address").strip(), lines[i - 1]
        name = title[: -len(address)].strip() if title.endswith(address) else title
        entry = {"name": name, "address": address, "city": match.group("city").strip(),
                 "status": None, "omzetplafond": False}
        for j in range(i + 1, min(i + 6, len(lines))):
            if j + 1 < len(lines) and _DISTANCE.match(lines[j + 1]):
                break  # lines[j] is the title of the next entry
            low = lines[j].lower()
            if low in STATUSES and entry["status"] is None:
                entry["status"] = STATUSES[low]
            elif low == "met omzetplafond":
                entry["omzetplafond"] = True
        if entry["status"]:
            entries.append(entry)
    return entries, total


def fetch_town(http: PoliteSession, category: str, town: str) -> tuple[list[dict], int | None, int, str]:
    """All entries for one category around one town, following result pages."""
    url, pages, found, total, seen, error = URL.format(category=category, town=town, year=YEAR), 0, [], None, set(), ""
    while url and pages < 15 and url not in seen:
        seen.add(url)
        try:
            resp = http.get(url)
        except Exception as exc:
            error = type(exc).__name__
            break
        pages += 1
        entries, count = parse_results(html_to_text(resp.text))
        total = total or count
        found += [dict(e, town=town, category=category, source_url=resp.url) for e in entries]
        nxt = [u for u in find_links(resp.text, resp.url, r"pagina=\d+") if u not in seen]
        url = nxt[0] if nxt and len(found) < (total or 0) else None
    return found, total, pages, error


def main(argv: list[str]) -> int:
    towns = TOWNS[: int(argv[0])] if argv else TOWNS
    http = PoliteSession(delay=3)
    report = ["# Zorgvinder CZ (contracten 2027)", "", f"Run: {today()}.", ""]
    categories = []
    for category in CATEGORIES:
        found, total, _, error = fetch_town(http, category, towns[0])
        report.append(f"- categorie `{category}`: {len(found)} gelezen, {total} genoemd {error}".rstrip())
        if found:
            categories.append(category)
    report += ["", "| categorie | plaats | genoemd | gelezen | pagina's |", "|---|---|---|---|---|"]
    rows = []
    for category in categories:
        for town in towns:
            found, total, pages, error = fetch_town(http, category, town)
            rows += found
            report.append(f"| {category} | {town} | {total if total is not None else '?'} | {len(found)} | {pages} {error} |")
            print(f"{category} {town}: {len(found)} of {total}")
    if not rows:
        print("No entries read from the CZ care finder", file=sys.stderr)
        return 1
    df = (pd.DataFrame(rows).drop_duplicates(["name", "address", "city"])
          .assign(concern="CZ", label="CZ", year=YEAR, source="CZ zorgvinder", fetched_on=today()))
    report += ["", f"Totaal: {len(df)} unieke locaties; status: "
               + ", ".join(f"{k} {v}" for k, v in df["status"].value_counts().items()) + "."]
    path = ROOT / "docs" / "data_inventory" / "cz_zorgvinder.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(report) + "\n", encoding="utf-8")
    save_with_history(df, "cz_zorgvinder", today())
    print(f"cz_zorgvinder.csv: {len(df)} locations")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
