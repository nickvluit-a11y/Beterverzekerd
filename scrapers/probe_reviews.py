"""Explore ZorgkaartNederland before collecting anything: what robots.txt allows and where a hospital
page shows its aggregate rating (average score + number of ratings).

Only aggregates will ever be stored (no review texts, no names of care providers), see CLAUDE.md.
Output: docs/data_inventory/reviews_probe.md

Usage: python -m scrapers.probe_reviews
"""

from __future__ import annotations

import json
import re
import sys

import requests

from scrapers.common import ROOT, USER_AGENT, PoliteSession, RobotsDisallowed, find_links, today

BASE = "https://www.zorgkaartnederland.nl"
LISTING = f"{BASE}/ziekenhuis"


def main() -> int:
    lines = ["# ZorgkaartNederland (verkenning)", "", f"Run: {today()}.", ""]
    try:
        robots = requests.get(f"{BASE}/robots.txt", headers={"User-Agent": USER_AGENT}, timeout=30)
        lines += [f"## robots.txt (HTTP {robots.status_code})", "", "```", robots.text[:3000], "```", ""]
    except Exception as exc:
        lines += [f"robots.txt niet op te halen: {exc}", ""]
    http = PoliteSession(delay=3)
    try:
        page = http.get(LISTING)
        hospitals = [u for u in find_links(page.text, page.url, r"/zorginstelling/") if "ziekenhuis" in u][:3]
        lines += [f"## Overzichtspagina {LISTING}", "", f"HTTP {page.status_code}, {len(page.text):,} tekens.",
                  "Voorbeeldlinks naar ziekenhuizen:", ""] + [f"- {u}" for u in hospitals] + [""]
        for url in hospitals[:2]:
            detail = http.get(url)
            ld = re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', detail.text, re.S)
            ratings = []
            for block in ld:
                try:
                    data = json.loads(block)
                except ValueError:
                    continue
                for item in data if isinstance(data, list) else [data]:
                    if isinstance(item, dict) and "aggregateRating" in item:
                        ratings.append(item["aggregateRating"])
            numbers = re.findall(r"(\d[,.]\d)\s*(?:uit|/)\s*10|(\d+)\s+waarderingen", detail.text)[:5]
            lines += [f"### {url}", "", f"- HTTP {detail.status_code}",
                      f"- JSON-LD aggregateRating: {ratings or 'niet gevonden'}",
                      f"- cijfers in tekst (eerste): {numbers or 'niet gevonden'}", ""]
    except RobotsDisallowed as exc:
        lines += [f"Niet toegestaan door robots.txt: {exc}", ""]
    except Exception as exc:
        lines += [f"Fout: {type(exc).__name__}: {str(exc)[:200]}", ""]
    path = ROOT / "docs" / "data_inventory" / "reviews_probe.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"written {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
