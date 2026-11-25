"""Contract status 2027 per hospital location from VGZ's own care finder (vgz.nl/zorgzoeker).

The finder page loads its results from VGZ's own JSON service (api.vgz.nl/zorgzoeker), the same
request a visitor's browser makes: hospitals and clinics ('zorgsoort' 015) around a postcode, 25
per page. Each result carries the AGB code, the postcode and the contract status, so linking to
our locations is exact. robots.txt is respected by PoliteSession; one request every few seconds.

Output: data/processed/vgz_zorgzoeker.csv (+ dated history), docs/data_inventory/vgz_zorgzoeker.md
Usage: python -m scrapers.vgz_zorgzoeker
"""

from __future__ import annotations

import sys
from urllib.parse import quote

import pandas as pd

from pipeline.reference import ROOT, save_with_history
from scrapers.common import PoliteSession, today

YEAR = 2027
URL = ("https://api.vgz.nl/zorgzoeker/api/v2/zorgaanbieder/zoekopzorgsoort/vgz/{year}/015?contractStatus=6"
       "&gebruikVerzorgingsgebieden=false&sortByGoodPractice=false&initieleZorgsoortCode=015&landCode=NL"
       "&postcode={postcode}&zoekRadius={radius}&sortering=AfstandOplopend&skip={skip}&take={take}&soortLocatie=3")
CENTRE, RADIUS, TAKE = "3584 CX", 300, 25  # 300 km around Utrecht covers the Netherlands

STATUSES = {  # VGZ contract status -> (our status, revenue cap)
    "Gecontracteerd": ("gecontracteerd", False),
    "GecontracteerdZonderDLP": ("gecontracteerd", True),  # VGZ: 'Contract: vergoed. Let op: hier is een omzetplafond'
    "GecontracteerdZKPBereikt": ("gecontracteerd", True),  # revenue cap reached
    "InOnderhandelingAltijdVergoed": ("vergoed_als_contract", False),
    "InOnderhandelingTijdensOnderhandelingVergoed": ("vergoed_als_contract", False),
    "InOnderhandeling": ("in_onderhandeling", False),
    "NietGecontracteerd": ("geen_contract", False),
    "Uitsluiting": ("geen_contract", False),
}
SPECIALISMS = {"Orthopedie": "orthopedie", "Oogheelkunde": "oogheelkunde"}  # kept for later, per procedure


def parse(result: dict) -> dict | None:
    info = result.get("basisInfo") or {}
    status, cap = STATUSES.get(str(info.get("contractStatus")), (None, False))
    if not status or not info.get("agbCode"):
        return None
    row = {"name": info.get("naam"), "agb": str(info["agbCode"]).zfill(8),
           "postcode": str(info.get("postcode") or "").replace(" ", "").upper(),
           "address": f"{info.get('straat') or ''} {info.get('huisnummer') or ''}".strip(),
           "city": str(info.get("plaatsnaam") or "").title(), "status": status, "omzetplafond": cap,
           "vgz_status": info.get("contractStatus")}
    for care in result.get("zorgsoorten") or []:
        for sub in care.get("subzorgsoorten") or []:
            if sub.get("zorgsoortNaam") in SPECIALISMS:
                row[f"status_{SPECIALISMS[sub['zorgsoortNaam']]}"] = sub.get("contractType")
    return row


def main(argv: list[str]) -> int:
    http = PoliteSession(delay=3)
    rows, total, skip, error = [], None, 0, ""
    while total is None or skip < total:
        url = URL.format(year=YEAR, postcode=quote(CENTRE), radius=RADIUS, skip=skip, take=TAKE)
        try:
            data = http.get(url).json()
        except Exception as exc:
            error = f"{type(exc).__name__}: {str(exc)[:200]}"
            break
        total = int(data.get("totaalAantalResultaten") or 0)
        page = [r for r in (parse(x) for x in data.get("zoekresultaat") or []) if r]
        if not data.get("zoekresultaat"):
            break
        rows += page
        skip += TAKE
        if skip > 5000:
            break
    report = ["# Zorgzoeker VGZ (contracten 2027)", "", f"Run: {today()}. Genoemd: {total}, gelezen: {len(rows)}.",
              f"Fout: {error}" if error else ""]
    if not rows:
        (ROOT / "docs" / "data_inventory" / "vgz_zorgzoeker.md").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("No entries read from the VGZ care finder", error, file=sys.stderr)
        return 1
    df = (pd.DataFrame(rows).drop_duplicates(["agb", "postcode", "name"])
          .assign(concern="VGZ", label="VGZ", year=YEAR, source="VGZ zorgzoeker",
                  source_url="https://www.vgz.nl/zorg-regelen/zorgzoeker", fetched_on=today()))
    report += ["", "Status: " + ", ".join(f"{k} {v}" for k, v in df["vgz_status"].value_counts().items()) + "."]
    (ROOT / "docs" / "data_inventory" / "vgz_zorgzoeker.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    save_with_history(df, "vgz_zorgzoeker", today())
    print(f"vgz_zorgzoeker.csv: {len(df)} locations of {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
