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
BASE = "https://zorgvinder.cz.nl/resultaten/{category}/{town}?jaar={year}&vergoedbv=ja%2Cinclafsp%2Cnogniet%2Cnee"
URL = BASE + "&afstand=25"
# the finder shows 30 results per page and pages with JavaScript; which parameters give 'heel
# Nederland' and the next page is found at run time (first candidate that works)
DISTANCE_CANDIDATES = ["", "&afstand=0", "&afstand=heel-nederland", "&afstand=999", "&afstand=100"]
PAGE_CANDIDATES = ["pagina", "page", "p", "paginanummer"]
# 'ziekenhuis' is known to work; the others are tried once (first town) and kept only if they list results
CATEGORIES = ["ziekenhuis", "zelfstandig-behandelcentrum"]  # both checked to exist (run 2026-11-25)
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


def fetch(http: PoliteSession, url: str) -> tuple[list[dict], int | None, str]:
    try:
        resp = http.get(url)
    except Exception as exc:
        return [], None, type(exc).__name__
    entries, total = parse_results(html_to_text(resp.text))
    return [dict(e, source_url=resp.url) for e in entries], total, ""


def _key(e: dict) -> tuple:
    return e["name"], e["address"], e["city"]


def discover(http: PoliteSession, report: list[str]) -> tuple[str, str] | None:
    """(distance suffix covering the most results, page parameter that gives new results)."""
    best = None
    for suffix in DISTANCE_CANDIDATES:
        found, total, error = fetch(http, BASE.format(category="ziekenhuis", town="utrecht", year=YEAR) + suffix)
        report.append(f"- afstand `{suffix or '(geen)'}`: {total} genoemd, {len(found)} gelezen {error}".rstrip())
        if found and (best is None or (total or 0) > best[1]):
            best = (suffix, total or 0, {_key(e) for e in found})
    if not best:
        return None
    suffix, _, first = best
    for param in PAGE_CANDIDATES:
        found, _, error = fetch(http, BASE.format(category="ziekenhuis", town="utrecht", year=YEAR) + suffix + f"&{param}=2")
        new = {_key(e) for e in found} - first
        report.append(f"- pagina-parameter `{param}`: {len(new)} nieuwe {error}".rstrip())
        if new:
            return suffix, param
    return None


def fetch_all(http: PoliteSession, category: str, suffix: str, param: str) -> tuple[list[dict], int | None, int]:
    """Every page of one category for the whole country."""
    rows, seen, total, page = [], set(), None, 1
    while page <= 150:
        url = BASE.format(category=category, town="utrecht", year=YEAR) + suffix + (f"&{param}={page}" if page > 1 else "")
        found, count, _ = fetch(http, url)
        total = total or count
        new = [e for e in found if _key(e) not in seen]
        if not new:
            break
        seen |= {_key(e) for e in new}
        rows += [dict(e, town="heel-nl", category=category) for e in new]
        if total and len(rows) >= total:
            break
        page += 1
    return rows, total, page


def main(argv: list[str]) -> int:
    towns = TOWNS[: int(argv[0])] if argv else TOWNS
    http = PoliteSession(delay=3)
    report = ["# Zorgvinder CZ (contracten 2027)", "", f"Run: {today()}.", "", "## Zoekinstellingen", ""]
    rows = []
    found_way = discover(http, report)
    if found_way:
        suffix, param = found_way
        report += ["", f"Heel Nederland met `{suffix or '(geen afstand)'}`, bladeren met `{param}`.", "",
                    "| categorie | genoemd | gelezen | pagina's |", "|---|---|---|---|"]
        for category in CATEGORIES:
            found, total, pages = fetch_all(http, category, suffix, param)
            rows += found
            report.append(f"| {category} | {total} | {len(found)} | {pages} |")
            print(f"{category}: {len(found)} of {total}")
    else:  # fallback: 25 km around many towns, first page only (30 results each)
        report += ["", "Geen manier gevonden om te bladeren: per plaats de eerste 30.", "",
                   "| categorie | plaats | genoemd | gelezen | pagina's |", "|---|---|---|---|---|"]
        for category in CATEGORIES:
            for town in towns:
                found, total, pages, error = fetch_town(http, category, town)
                rows += found
                report.append(f"| {category} | {town} | {total if total is not None else '?'} | {len(found)} | {pages} {error} |")
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
