"""Download the official Zorginzicht 'indicatorengidsen' for our procedures and keep their text.

The guides define every indicator (numerator, denominator, direction, PROM scales, case-mix
correction). Their text is committed to docs/data_inventory/guides/ so indicator rules in
data/manual/indicators.csv can be checked line by line against the source.

Usage: python -m scrapers.indicator_guides
"""

from __future__ import annotations

import sys

from scrapers.common import ROOT, PoliteSession
from scrapers.contracts import extract_pdf

GUIDES = {
    "thp_2024": "https://www.zorginzicht.nl/static/prozin_bijlage/0dafd763-6060-4478-a724-27d21f6759c7-indicatorengids-heupprothese---thp-verslagjaar-2024.pdf",
    "thp_2025": "https://www.zorginzicht.nl/binaries/content/assets/zorginzicht/kwaliteitsinstrumenten/indicatorengids-heupprothese---thp-verslagjaar-2025.pdf",
    "tkp_2024": "https://www.zorginzicht.nl/static/prozin_bijlage/62faf592-3c73-44e9-b660-888ec04dca43-indicatorengids-knieprothese---tkp-verslagjaar-2024.pdf",
    "tkp_2025": "https://www.zorginzicht.nl/static/prozin_bijlage/0a59ce8d-eb20-4b48-90a3-807922d70fc5-indicatorengids-knieprothese---tkp-verslagjaar-2025.pdf",
    "cataract_2024": "https://www.zorginzicht.nl/static/prozin_bijlage/40b393ea-9dcb-44ca-8983-6870267a56e3-indicatorengids-cataract---verslagjaar-2024.pdf",
    "cataract_2025": "https://www.zorginzicht.nl/binaries/content/assets/zorginzicht/kwaliteitsinstrumenten/indicatorengids-cataract---verslagjaar-2025.pdf",
}
OUT = ROOT / "docs" / "data_inventory" / "guides"


def main() -> int:
    http = PoliteSession()
    OUT.mkdir(parents=True, exist_ok=True)
    ok = 0
    for name, url in GUIDES.items():
        try:
            resp = http.get(url)
            text, _ = extract_pdf(resp.content)
        except Exception as exc:
            print(f"FAIL {name}: {exc}", file=sys.stderr)
            continue
        (OUT / f"{name}.txt").write_text(f"source: {url}\n\n{text}", encoding="utf-8")
        ok += 1
        print(f"ok   {name}: {len(text):,} characters")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
