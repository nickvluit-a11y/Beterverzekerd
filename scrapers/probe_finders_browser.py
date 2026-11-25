"""Open the JavaScript care finders of the insurers in scope in a headless browser and record how
they get their data: the JSON responses the page itself loads, and the rendered text after a
search for hospitals near Utrecht. Only looks; one page load per finder, robots.txt respected.

Output: docs/data_inventory/finder_browser_<brand>.md (endpoints + sample) and
        docs/data_inventory/finder_browser_<brand>.txt (rendered text)
Usage: python -m scrapers.probe_finders_browser
Needs: pip install playwright && python -m playwright install chromium (done in CI)
"""

from __future__ import annotations

import json
import re
import sys
import urllib.robotparser
from urllib.parse import urlparse

from scrapers.common import ROOT, USER_AGENT, today

FINDERS = {  # start pages of the finders, searching hospitals near Utrecht where the URL allows it
    "zilveren_kruis": "https://www.zilverenkruis.nl/consumenten/zorgzoeker/resultaten?zorgsoort=ziekenhuis&locatie=Utrecht",
    "vgz": "https://www.vgz.nl/zorg-regelen/zorgzoeker/zoekresultaten?zoekterm=ziekenhuis&locatie=Utrecht",
    "menzis": "https://www.menzis.nl/zorgzoeker",
}
OUT = ROOT / "docs" / "data_inventory"


def allowed(url: str) -> bool:
    parts = urlparse(url)
    robots = urllib.robotparser.RobotFileParser(f"{parts.scheme}://{parts.netloc}/robots.txt")
    try:
        robots.read()
    except Exception:
        return True  # no readable robots.txt: allowed by convention
    return robots.can_fetch(USER_AGENT, url)


def probe(page, name: str, url: str) -> list[str]:
    lines = [f"# Zorgzoeker {name} (browser-verkenning {today()})", "", f"- start: {url}"]
    if not allowed(url):
        return lines + ["- robots.txt staat dit niet toe: niet geopend"]
    seen: list[dict] = []

    def on_response(resp):
        ctype = resp.headers.get("content-type", "")
        if "json" in ctype and len(seen) < 60:
            try:
                body = resp.text()
            except Exception:
                body = ""
            seen.append({"url": resp.url, "status": resp.status, "method": resp.request.method,
                         "size": len(body), "sample": body[:1500]})

    page.on("response", on_response)
    try:
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(4000)
    except Exception as exc:
        lines.append(f"- laden: {type(exc).__name__}: {str(exc)[:200]}")
    text = page.inner_text("body") if page.url else ""
    (OUT / f"finder_browser_{name}.txt").write_text(f"source: {page.url}\n\n{text[:60000]}", encoding="utf-8")
    links = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
    finder_links = sorted({l for l in links if re.search(r"zorgzoeker|zorgverlener|zorgaanbieder", l, re.I)})[:40]
    lines += [f"- eind-URL: {page.url}", f"- zichtbare tekst: {len(text):,} tekens", "",
              "## JSON-antwoorden die de pagina zelf laadt", ""]
    for r in sorted(seen, key=lambda r: -r["size"]):
        lines += [f"### {r['method']} {r['status']} {r['url']} ({r['size']:,} tekens)", "", "```",
                  r["sample"].replace("```", "'''"), "```", ""]
    lines += ["## Links naar zorgzoeker-pagina's", ""] + [f"- {l}" for l in finder_links]
    page.remove_listener("response", on_response)
    return lines


def main() -> int:
    from playwright.sync_api import sync_playwright
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(user_agent=USER_AGENT, locale="nl-NL")
        for name, url in FINDERS.items():
            try:
                lines = probe(page, name, url)
            except Exception as exc:
                lines = [f"# Zorgzoeker {name}", "", f"- fout: {type(exc).__name__}: {str(exc)[:300]}"]
            (OUT / f"finder_browser_{name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"probed {name}")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
