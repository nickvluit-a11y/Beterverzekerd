"""Use the JavaScript care finders of Zilveren Kruis, VGZ and Menzis the way a visitor does, in a
headless browser, and record how they get their data: the form fields, the JSON responses the page
loads after a search for hospitals near 3584 CX, and the rendered result text. Only looks: one
search per finder, marketing cookies refused, robots.txt respected.

Output: docs/data_inventory/finder_browser_<brand>.md (+ .txt with the rendered results)
Usage: python -m scrapers.probe_finders_browser
Needs: pip install playwright && python -m playwright install chromium (done in CI)
"""

from __future__ import annotations

import re
import sys
import urllib.robotparser
from urllib.parse import urlparse

from scrapers.common import ROOT, USER_AGENT, today

FINDERS = {  # landing page, field 'what', field 'where', link to click first, how to submit ('enter' or a selector)
    "zilveren_kruis": ("https://www.zilverenkruis.nl/consumenten/zorgzoeker",
                       "#autofill-Zorgtype-input", "#autofill-Locatie-input", None,
                       "form:has(#autofill-Locatie-input) button[type=submit], form:has(#autofill-Locatie-input) button"),
    "vgz": ("https://www.vgz.nl/zorg-regelen/zorgzoeker", "input[name=zoekterm]", "input[name=locatie]", None, "enter"),
    "menzis": ("https://www.menzis.nl/zorg-en-vergoedingen/de-zorgvinder", None, None, "Naar de Zorgvinder",
               "button:has-text('Zoeken')"),
}
WHAT, WHERE = "Ziekenhuis", "3584 CX"
_FINDER_LINK = re.compile(r"zorgzoeker|zorgverlener (zoeken|vinden)|zoek een zorgverlener|vind een zorgverlener", re.I)
_WHAT_FIELD = re.compile(r"zorg|wat|zoek|naam|behandel|specialisme", re.I)
_WHERE_FIELD = re.compile(r"postcode|plaats|locatie|waar|adres", re.I)
OUT = ROOT / "docs" / "data_inventory"


def allowed(url: str) -> bool:
    parts = urlparse(url)
    robots = urllib.robotparser.RobotFileParser(f"{parts.scheme}://{parts.netloc}/robots.txt")
    try:
        robots.read()
    except Exception:
        return True
    return robots.can_fetch(USER_AGENT, url)


def refuse_cookies(page) -> None:
    for text in ("Weigeren", "Alleen noodzakelijke", "Alleen functionele", "Nee, bedankt", "Accepteren"):
        button = page.get_by_role("button", name=re.compile(text, re.I))
        if button.count():
            try:
                button.first.click(timeout=3000)
                page.wait_for_timeout(1000)
                return
            except Exception:
                continue


def fields(page) -> list[dict]:
    return page.eval_on_selector_all(
        "input:not([type=hidden]):not([type=checkbox]):not([type=radio]), select",
        """els => els.map(e => ({tag: e.tagName, type: e.type, name: e.name, id: e.id,
            placeholder: e.placeholder || '', aria: e.getAttribute('aria-label') || '',
            label: (e.labels && e.labels[0] ? e.labels[0].innerText : '')}))""")


def describe(f: dict) -> str:
    return " ".join(str(f.get(k) or "") for k in ("name", "id", "placeholder", "aria", "label"))


def fill(page, selector: str, value: str) -> str:
    """Type into the visible field and pick the first suggestion, as a visitor does."""
    field = page.locator(selector).locator("visible=true").first
    if not field.count():
        field = page.locator(selector).first
    try:
        field.click(timeout=5000)
        field.fill("")
        field.type(value, delay=60)
    except Exception:  # covered by an overlay or hidden: set it directly
        field.fill(value, force=True)
    page.wait_for_timeout(2000)
    options = page.get_by_role("option").locator("visible=true")
    if options.count():
        options.first.click(timeout=3000)
        return f"gekozen suggestie voor {value}"
    return f"ingevuld {value}"


def probe(page, name: str, url: str, what_sel: str | None = None, where_sel: str | None = None,
          link_text: str | None = None, submit: str = "enter") -> list[str]:
    lines = [f"# Zorgzoeker {name} (browser-verkenning {today()})", "", f"- start: {url}"]
    if not allowed(url):
        return lines + ["- robots.txt staat dit niet toe: niet geopend"]
    seen: list[dict] = []

    def on_response(resp):
        if "json" in resp.headers.get("content-type", "") and len(seen) < 80:
            try:
                body = resp.text()
            except Exception:
                body = ""
            seen.append({"url": resp.url, "status": resp.status, "method": resp.request.method,
                         "post": (resp.request.post_data or "")[:1500], "size": len(body), "sample": body[:3000],
                         "full": body if len(body) > 2000 and "cookielaw" not in resp.url else ""})

    page.on("response", on_response)
    page.goto(url, wait_until="networkidle", timeout=60000)
    refuse_cookies(page)
    if link_text:
        link = page.get_by_role("link", name=re.compile(link_text, re.I))
        target = link.first.get_attribute("href") if link.count() else None
        lines.append(f"- link '{link_text}': {target}")
        if target:
            target = page.evaluate("h => new URL(h, location.href).href", target)
            if allowed(target):
                page.goto(target, wait_until="networkidle", timeout=60000)
                refuse_cookies(page)
    if not what_sel and not any(_WHERE_FIELD.search(describe(f)) for f in fields(page)):
        links = page.eval_on_selector_all("a[href]", "els => els.map(e => [e.href, e.innerText])")
        host = urlparse(page.url).netloc
        target = next((h for h, t in links if urlparse(h).netloc == host and (_FINDER_LINK.search(t or "")
                       or "zorgzoeker" in h.lower() or "zorgvinder" in h.lower())), None)
        lines.append(f"- link naar zoeker: {target}")
        if target and allowed(target):
            page.goto(target, wait_until="networkidle", timeout=60000)
            refuse_cookies(page)
    form = fields(page)
    lines += [f"- zoekpagina: {page.url}", "", "## Invoervelden", ""] + [f"- {describe(f).strip()} ({f['tag']}/{f['type']})" for f in form]
    before = len(seen)
    form_fields = [f for f in form if not re.search(r"header|nav|cookie|vendor", describe(f), re.I)]
    sel = lambda f: f"#{f['id']}" if f.get("id") else f"[name='{f['name']}']" if f.get("name") else None
    what_sel = what_sel or next((sel(f) for f in form_fields if _WHAT_FIELD.search(describe(f))
                                 and not _WHERE_FIELD.search(describe(f))), None)
    where_sel = where_sel or next((sel(f) for f in form_fields if _WHERE_FIELD.search(describe(f))), None)
    for selector, value in ((what_sel, WHAT), (where_sel, WHERE)):
        if not selector:
            lines.append(f"- geen veld voor {value}")
            continue
        try:
            lines.append(f"- {selector}: {fill(page, selector, value)}")
        except Exception as exc:
            lines.append(f"- {selector} ({value}): {type(exc).__name__}: {str(exc)[:150]}")
    try:  # submit inside the finder's own form (the site's header search also says 'Zoeken')
        if submit == "enter":
            page.locator(where_sel or what_sel).first.press("Enter", timeout=5000)
        else:
            button = page.locator(submit).locator("visible=true")
            lines.append(f"- zoekknoppen gevonden: {button.count()}")
            button.first.click(timeout=5000)
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception as exc:
        lines.append(f"- zoeken: {type(exc).__name__}")
    page.wait_for_timeout(5000)
    text = page.inner_text("body")
    (OUT / f"finder_browser_{name}.txt").write_text(f"source: {page.url}\n\n{text[:60000]}", encoding="utf-8")
    lines += ["", f"- na zoeken: {page.url}", f"- zichtbare tekst: {len(text):,} tekens",
              f"- JSON-antwoorden voor/na zoeken: {before}/{len(seen) - before}", "",
              "## JSON-antwoorden na het zoeken (grootste eerst)", ""]
    biggest = max(seen[before:], key=lambda r: r["size"], default=None)
    if biggest and biggest["size"] > 2000:
        (OUT / f"finder_browser_{name}.json").write_text(biggest.get("full", "")[:1_500_000], encoding="utf-8")
        lines += [f"Volledige data van de grootste aanroep: finder_browser_{name}.json", ""]
    for r in sorted(seen[before:], key=lambda r: -r["size"]):
        if "cookielaw" in r["url"] or "applicationinsights" in r["url"] or "monitor.azure" in r["url"]:
            continue
        lines += [f"### {r['method']} {r['status']} {r['url']} ({r['size']:,} tekens)", ""]
        if r["post"]:
            lines += ["Verzonden:", "```", r["post"], "```"]
        lines += ["```", r["sample"].replace("```", "'''"), "```", ""]
    page.remove_listener("response", on_response)
    return lines


def main() -> int:
    from playwright.sync_api import sync_playwright
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, (url, what_sel, where_sel, link_text, submit) in FINDERS.items():
            page = browser.new_page(user_agent=USER_AGENT, locale="nl-NL")
            try:
                lines = probe(page, name, url, what_sel, where_sel, link_text, submit)
            except Exception as exc:
                lines = [f"# Zorgzoeker {name}", "", f"- fout: {type(exc).__name__}: {str(exc)[:300]}"]
            page.close()
            (OUT / f"finder_browser_{name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"probed {name}")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
