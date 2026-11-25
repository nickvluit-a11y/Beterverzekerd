"""Explore the care finders ('zorgzoekers') of the insurers: they publish, per insurer, the contract
status of every hospital, so one source per insurer could close the contract gap.

This probe only looks: for each finder page it records whether robots.txt allows it, the HTTP
status, the scripts it loads and every URL in the page that looks like a data endpoint (api, json,
graphql, search). Output: docs/data_inventory/insurer_finders.md, read by a human (or Claude) to
decide which finder can be read politely and how.

Usage: python -m scrapers.probe_insurers
"""

from __future__ import annotations

import re
import sys

from scrapers.common import ROOT, PoliteSession, RobotsDisallowed, today

FINDERS = {
    "CZ": "https://zorgvinder.cz.nl/resultaten/ziekenhuis/utrecht?afstand=10&jaar=2027",
    "VGZ": "https://www.vgz.nl/zorg-regelen/zorgzoeker",
    "Zilveren Kruis": "https://www.zilverenkruis.nl/consumenten/zorgzoeker",
    "Menzis": "https://www.menzis.nl/zorgzoeker",
    "DSW": "https://www.dsw.nl/consumenten/zorgzoeker",
    "a.s.r.": "https://www.asr.nl/zorgverzekering/zorgzoeker",
    "Zorg en Zekerheid": "https://www.zorgenzekerheid.nl/zorgzoeker",
    "ONVZ": "https://www.onvz.nl/zorgzoeker",
}
_URL = re.compile(r"""https?://[^\s"'<>\\)]+""")
_ENDPOINT = re.compile(r"api|json|graphql|search|zoek|zorgaanbieder|provider|contract", re.IGNORECASE)
_SCRIPT = re.compile(r"""<script[^>]+src=["']([^"']+)["']""", re.IGNORECASE)


def probe(http: PoliteSession, name: str, url: str) -> list[str]:
    lines = [f"## {name}", "", f"- URL: {url}"]
    try:
        resp = http.get(url)
    except RobotsDisallowed as exc:
        return lines + [f"- robots.txt: niet toegestaan ({exc})", ""]
    except Exception as exc:
        return lines + [f"- fout: {type(exc).__name__}: {str(exc)[:200]}", ""]
    page = resp.text
    endpoints = sorted({u.rstrip(".,;") for u in _URL.findall(page) if _ENDPOINT.search(u)})[:40]
    scripts = sorted(set(_SCRIPT.findall(page)))[:25]
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)\b.*?</\1>", " ", page, flags=re.S | re.I)))
    lines += [f"- status: {resp.status_code}, eind-URL: {resp.url}, {len(page):,} tekens HTML",
              f"- zichtbare tekst (begin): {text.strip()[:400]}", "", "Mogelijke data-endpoints:", ""]
    lines += [f"- {u}" for u in endpoints] or ["- (geen)"]
    lines += ["", "Scripts:", ""] + ([f"- {s}" for s in scripts] or ["- (geen)"]) + [""]
    return lines


def main() -> int:
    http = PoliteSession()
    lines = ["# Zorgzoekers van verzekeraars (verkenning)", "", f"Run: {today()}. Alleen kijken, niets massaal ophalen.", ""]
    for name, url in FINDERS.items():
        lines += probe(http, name, url)
        print(f"probed {name}")
    path = ROOT / "docs" / "data_inventory" / "insurer_finders.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
