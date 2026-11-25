"""Check every 2027 premium against the insurer's own website.

For each label we start from its own pages (the source_url when it is on the insurer's domain, plus
the label's home page), follow same-site links that look like premium or basic-insurance pages
(also PDFs), and look for the policy's monthly premium written the Dutch way ('159,45'). A premium
counts as confirmed when that amount appears on a page of the insurer itself; the page is recorded.

Output: data/processed/premium_check.csv (label, polis, premie, confirmed, confirmed_url, checked_on)
        docs/data_inventory/premie_controle.md
Usage: python -m scrapers.verify_premiums [label ...]
"""

from __future__ import annotations

import io
import re
import sys
from urllib.parse import urlparse

import pandas as pd

from pipeline.reference import MANUAL, PROCESSED, ROOT
from scrapers.common import PoliteSession, all_links, today
from scrapers.contracts import html_to_text

SITES = {  # label -> the insurer's own site (not comparison sites)
    "Zilveren Kruis": "https://www.zilverenkruis.nl", "FBTO": "https://www.fbto.nl",
    "Interpolis": "https://www.interpolis.nl", "De Friesland": "https://www.defriesland.nl",
    "ZieZo": "https://www.ziezo.nl", "De christelijke zorgverzekeraar": "https://www.dezorgverzekeraar.nl",
    "VGZ": "https://www.vgz.nl", "Bewuzt": "https://www.bewuzt.nl", "IZA": "https://www.iza.nl",
    "IZZ": "https://www.izz.nl", "UMC Zorgverzekering": "https://www.umczorgverzekering.nl",
    "UnitedConsumers": "https://www.unitedconsumers.com", "Univé": "https://www.unive.nl",
    "ONVZ": "https://www.onvz.nl", "CZ": "https://www.cz.nl", "OHRA": "https://www.ohra.nl",
    "Nationale-Nederlanden": "https://www.nn.nl", "CZdirect": "https://www.czdirect.nl", "Just": "https://www.just.nl",
    "Menzis": "https://www.menzis.nl", "VinkVink": "https://www.vinkvink.nl", "DSW": "https://www.dsw.nl",
    "Stad Holland": "https://www.stadholland.nl", "a.s.r.": "https://www.asr.nl", "Ik kies zelf": "https://www.ikkieszelf.nl",
    "Zorg en Zekerheid": "https://www.zorgenzekerheid.nl", "Salland": "https://www.salland.nl",
    "HollandZorg": "https://www.hollandzorg.com", "Aevitae": "https://www.aevitae.com", "Care4Life": "https://www.care4life.nl",
}
_FOLLOW = re.compile(r"premie|basisverzekering|zorgverzekering|polis|tarie", re.IGNORECASE)
MAX_PAGES = 25


def amount_text(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def site_of(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def page_text(resp) -> str:
    if "pdf" in resp.headers.get("content-type", "").lower() or resp.url.lower().endswith(".pdf"):
        import pdfplumber
        with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages[:30])
    return html_to_text(resp.text)


def find_amounts(text: str, amounts: dict[str, str]) -> set[str]:
    """Keys of `amounts` whose Dutch-formatted value appears in the text (also as '€ 159,45')."""
    flat = re.sub(r"\s+", " ", text)
    return {key for key, a in amounts.items() if re.search(rf"(?<![\d,.]){re.escape(a)}(?!\d)", flat)}


def check_label(http: PoliteSession, label: str, rows: pd.DataFrame) -> list[dict]:
    home = SITES.get(label)
    starts = [u for u in rows["source_url"].dropna().unique() if home and site_of(u) == site_of(home)]
    queue = list(dict.fromkeys(starts + ([home] if home else [])))
    amounts = {r.polis: amount_text(float(r.premie_per_maand)) for r in rows.itertuples() if pd.notna(r.premie_per_maand)}
    confirmed: dict[str, str] = {}
    seen, pages, errors = set(), 0, []
    while queue and pages < MAX_PAGES and len(confirmed) < len(amounts):
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            resp = http.get(url)
        except Exception as exc:
            errors.append(f"{url}: {type(exc).__name__}")
            continue
        pages += 1
        text = page_text(resp)
        if "2027" in text:
            for polis in find_amounts(text, amounts) - set(confirmed):
                confirmed[polis] = resp.url
        if "html" in resp.headers.get("content-type", "html"):
            for link, label_text in all_links(resp.text, resp.url):
                link = link.split("#")[0]
                if site_of(link) == site_of(home or url) and link not in seen \
                        and (_FOLLOW.search(link) or _FOLLOW.search(label_text or "")):
                    queue.append(link)
    out = []
    for r in rows.itertuples():
        out.append({"label": label, "polis": r.polis, "premie": r.premie_per_maand,
                    "confirmed": r.polis in confirmed, "confirmed_url": confirmed.get(r.polis),
                    "pages_checked": pages, "errors": "; ".join(errors[:3]), "checked_on": today()})
    return out


def main(argv: list[str]) -> int:
    from pipeline.reference import scope
    policies = pd.read_csv(MANUAL / "polissen_2027.csv")
    in_scope = policies[policies["concern"].isin(scope()["concern"]) & (policies["label"] != "ONVZ")]
    labels = argv or list(dict.fromkeys(in_scope["label"]))  # only the groups the app covers
    http = PoliteSession(delay=2)
    rows = []
    for label in labels:
        rows += check_label(http, label, policies[policies["label"] == label])
        print(f"{label}: {sum(r['confirmed'] for r in rows if r['label'] == label)} confirmed")
    df = pd.DataFrame(rows)
    df.to_csv(PROCESSED / "premium_check.csv", index=False)
    lines = ["# Controle premies 2027 op de eigen site van de verzekeraar", "", f"Run: {today()}. "
             f"{int(df['confirmed'].sum())} van {len(df)} polissen bevestigd.", "",
             "| label | polis | premie | bevestigd op |", "|---|---|---|---|"]
    lines += [f"| {r.label} | {r.polis} | {r.premie} | {r.confirmed_url or 'niet gevonden ' + (r.errors or '')} |"
              for r in df.itertuples()]
    path = ROOT / "docs" / "data_inventory" / "premie_controle.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
