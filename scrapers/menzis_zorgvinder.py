"""Contract status 2027 per hospital location from Menzis's own care finder (zorgvinder.menzis.nl).

The finder page asks Menzis's own JSON service for hospitals and clinics ('ziekenhuis / zbc')
around a postcode; each result has the AGB code, the address and, per insurance package, the
contract status for 2027. We make the same query for the whole country, page by page.
robots.txt is respected by PoliteSession; one request every few seconds.

Output: data/processed/menzis_zorgvinder.csv (+ dated history), docs/data_inventory/menzis_zorgvinder.md
Usage: python -m scrapers.menzis_zorgvinder
"""

from __future__ import annotations

import sys

import pandas as pd

from pipeline.reference import ROOT, save_with_history
from scrapers.common import PoliteSession, today

YEAR = 2027
URL = "https://zorgvinder.menzis.nl/api/zadvies/MENZIS_ZZ/zorginkoop/zorgaanbieders"
# the query the finder itself sends for 'ziekenhuis / zbc' (seen in docs/data_inventory/finder_browser_menzis.md)
QUERY = {"zorgaanbieder": {"type": ""}, "locatiebepaling": {"afstandKm": 300, "postcode": "3584CX"},
         "pakketIds": ["H231538222"], "pakketLijst": f"voor_advies_{YEAR}", "zoektermId": "1140736692",
         "specialismeIds": ["220906197"], "aannameNieuwePatienten": False}
PAGE = 50

STATUSES = {
    "GECONTRACTEERD": "gecontracteerd",
    "GEEN_CONTRACT_WEL_VERGOED": "vergoed_als_contract",  # finder: '(Nog) geen contract: wel vergoed'
    "IN_ONDERHANDELING": "in_onderhandeling",  # finder: 'Nog geen contract: een deel niet vergoed'
    "GEEN_CONTRACT": "geen_contract",
    "NIET_GECONTRACTEERD": "geen_contract",
}


def parse(item: dict) -> dict | None:
    package = next((p for p in item.get("pakketten") or [] if p.get("jaar") == YEAR), None)
    status = STATUSES.get(str((package or {}).get("contractStatus")))
    if not status or not item.get("agbCode"):
        return None
    return {"name": item.get("naamVestiging") or item.get("naam"), "agb": str(item["agbCode"]).zfill(8),
            "postcode": str(item.get("postcode") or "").replace(" ", "").upper(),
            "address": f"{item.get('straat') or ''} {item.get('huisnummer') or ''}".strip(),
            "city": item.get("plaats"), "status": status,
            "omzetplafond": str(package.get("omzetplafond")).upper() == "JA",
            "menzis_status": package.get("contractStatus")}


def main(argv: list[str]) -> int:
    http = PoliteSession(delay=3)
    rows, total, offset, error = [], None, 0, ""
    while total is None or offset < total:
        body = dict(QUERY, paginaEnSortering={"offset": offset, "aantal": PAGE, "sortering": "afstand"})
        try:
            data = http.post_json(URL, body).json()
        except Exception as exc:
            error = f"{type(exc).__name__}: {str(exc)[:200]}"
            break
        total = int(data.get("aantal") or 0)
        items = data.get("zorgaanbieders") or []
        if not items:
            break
        rows += [r for r in map(parse, items) if r]
        offset += len(items)
        if offset > 6000:
            break
    report = ["# Zorgvinder Menzis (contracten 2027)", "", f"Run: {today()}. Genoemd: {total}, gelezen: {len(rows)}.",
              f"Fout: {error}" if error else ""]
    path = ROOT / "docs" / "data_inventory" / "menzis_zorgvinder.md"
    if not rows:
        path.write_text("\n".join(report) + "\n", encoding="utf-8")
        print("No entries read from the Menzis care finder", error, file=sys.stderr)
        return 1
    df = (pd.DataFrame(rows).drop_duplicates(["agb", "postcode", "name"])
          .assign(concern="Menzis", label="Menzis", year=YEAR, source="Menzis zorgvinder",
                  source_url="https://zorgvinder.menzis.nl", fetched_on=today()))
    report += ["", "Status: " + ", ".join(f"{k} {v}" for k, v in df["menzis_status"].value_counts().items()) + "."]
    path.write_text("\n".join(report) + "\n", encoding="utf-8")
    save_with_history(df, "menzis_zorgvinder", today())
    print(f"menzis_zorgvinder.csv: {len(df)} locations of {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
