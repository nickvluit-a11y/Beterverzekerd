"""Contract status 2027 per hospital location from Zilveren Kruis's own care finder.

The finder page (zilverenkruis.nl/consumenten/zorgzoeker) asks Zilveren Kruis's own service for
hospitals ('Ziekenhuis', care type 1861) around a place, for a chosen basic policy. Each result has
the AGB number, the address, the contract status for 2027 and whether a revenue cap applies. We ask
the same for a list of towns that covers the country (each answer reaches about 40 km), for the
natura policy Basis Zeker. robots.txt is respected by PoliteSession; one request every few seconds.

Output: data/processed/zk_zorgzoeker.csv (+ dated history), docs/data_inventory/zk_zorgzoeker.md
Usage: python -m scrapers.zk_zorgzoeker
"""

from __future__ import annotations

import sys

import pandas as pd

from pipeline.reference import ROOT, save_with_history
from scrapers.common import PoliteSession, today
from scrapers.cz_zorgvinder import TOWNS

YEAR = 2027
BASE = "https://www.zilverenkruis.nl/clientcontroller/zorgzoekerclient/"
CARE_TYPE = "1861"  # 'Ziekenhuis' in the finder
POLICY = ("100", "Basis Zeker")  # value the finder sends for this basic policy (seen in the browser probe)

STATUSES = {
    "contract: vergoed": "gecontracteerd",
    "nog geen contract: wel vergoed": "vergoed_als_contract",
    "nog geen contract: een deel niet vergoed": "in_onderhandeling",
    "geen contract: een deel niet vergoed": "geen_contract",
}


def parse(result: dict) -> dict | None:
    contracts = [c for c in result.get("Contracten") or [] if str(c.get("Begindatum", "")).startswith(str(YEAR))] \
        or (result.get("Contracten") or [])
    if not contracts or not result.get("AGBNummer"):
        return None
    contract = contracts[0]
    status = STATUSES.get(str(contract.get("StatusOmschrijving", "")).strip().lower())
    if not status:
        return None
    address = result.get("Adres") or {}
    return {"name": result.get("Naam"), "agb": str(result["AGBNummer"]).zfill(8),
            "postcode": str(address.get("Postcode") or "").replace(" ", "").upper(),
            "address": f"{address.get('Straat') or ''} {address.get('Huisnummer') or ''}".strip(),
            "city": str(address.get("Plaats") or "").title(), "status": status,
            "omzetplafond": bool(contract.get("IsPlafondafspraakAanwezig")),
            "zk_status": contract.get("StatusOmschrijving")}


def main(argv: list[str]) -> int:
    http = PoliteSession(delay=3)
    rows, report = [], ["# Zorgzoeker Zilveren Kruis (contracten 2027)", "", f"Run: {today()}. Polis: {POLICY[1]}.", "",
                        "| plaats | genoemd | gelezen |", "|---|---|---|"]
    for town in TOWNS:
        try:
            place = http.post_json(BASE + "getautofilllocatie", {"ZoekstringLocatie": town.replace("-", " ")}).json()
            location_id = (place.get("options") or [{}])[0].get("id")
            if not location_id:
                report.append(f"| {town} | plaats niet gevonden | |")
                continue
            data = http.post_json(BASE + "getzorgaanbieders", {
                "Zorgtype": CARE_TYPE, "LocatieId": str(location_id), "Basisverzekering": POLICY[0],
                "Peildatum": f"{YEAR}-01-01T00:00:00.000Z"}).json()
        except Exception as exc:
            report.append(f"| {town} | fout: {type(exc).__name__} | |")
            continue
        found = [r for r in map(parse, data.get("Resultaten") or []) if r]
        rows += found
        report.append(f"| {town} | {data.get('AantalResultaten')} | {len(found)} |")
    path = ROOT / "docs" / "data_inventory" / "zk_zorgzoeker.md"
    if not rows:
        path.write_text("\n".join(report) + "\n", encoding="utf-8")
        print("No entries read from the Zilveren Kruis care finder", file=sys.stderr)
        return 1
    df = (pd.DataFrame(rows).drop_duplicates(["agb", "postcode", "name"])
          .assign(concern="Achmea", label="Zilveren Kruis", year=YEAR, source="Zilveren Kruis zorgzoeker",
                  source_url="https://www.zilverenkruis.nl/consumenten/zorgzoeker", fetched_on=today()))
    report += ["", f"Totaal: {len(df)} unieke locaties; status: "
               + ", ".join(f"{k} {v}" for k, v in df["zk_status"].value_counts().items()) + "."]
    path.write_text("\n".join(report) + "\n", encoding="utf-8")
    save_with_history(df, "zk_zorgzoeker", today())
    print(f"zk_zorgzoeker.csv: {len(df)} locations")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
