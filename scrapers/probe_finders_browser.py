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
                       "last:button:has-text('Zoeken')"),
    "vgz": ("https://www.vgz.nl/zorg-regelen/zorgzoeker", "input[name=zoekterm]", "input[name=locatie]", None, "enter"),
    "cz": ("https://zorgvinder.cz.nl/resultaten/ziekenhuis/utrecht?afstand=999&jaar=2027", "-", "-", None, "none"),
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


def next_page(page) -> list[str]:
    """Click 'next page' / 'more results' and report the URL and requests that follow."""
    out, before = [], page.url
    links = page.eval_on_selector_all("a[href]", "els => els.map(e => [e.href, e.innerText.trim(), e.getAttribute('aria-label') || ''])")
    out.append("- links met pagina/volgende: " + "; ".join(f"{t or a} -> {h}" for h, t, a in links
                                                         if re.search(r"pagina|page|volgende|next|meer", f"{h} {t} {a}", re.I))[:800])
    for pattern in (r"volgende|next", r"meer (resultaten|laden|tonen)|toon meer|laad meer", r"^\s*2\s*$"):
        target = page.get_by_role("link", name=re.compile(pattern, re.I)).or_(
            page.get_by_role("button", name=re.compile(pattern, re.I))).locator("visible=true")
        if target.count():
            try:
                target.first.click(timeout=5000)
                page.wait_for_load_state("networkidle", timeout=20000)
                out.append(f"- geklikt op '{pattern}': URL {before} -> {page.url}")
                break
            except Exception as exc:
                out.append(f"- klikken '{pattern}': {type(exc).__name__}")
    return out


def choose_policy(page, policy: str) -> list[str]:
    """Answer 'Kies je basisverzekering': list the choices, pick `policy`, confirm with 'Klaar'."""
    out = []
    selects = page.locator("select")
    for i in range(selects.count()):
        options = selects.nth(i).locator("option")
        texts = [options.nth(j).inner_text().strip() for j in range(options.count())]
        values = [options.nth(j).get_attribute("value") for j in range(options.count())]
        out.append(f"- keuzelijst {i}: " + "; ".join(f"{t}={v}" for t, v in zip(texts, values))[:600])
        match = next((v for t, v in zip(texts, values) if policy.lower() in t.lower()), None)
        if match:
            try:
                selects.nth(i).select_option(match, timeout=5000)
                out.append(f"- gekozen: {policy} ({match})")
            except Exception as exc:
                out.append(f"- kiezen {policy}: {type(exc).__name__}")
    if not any("gekozen" in o for o in out):  # a custom list instead of <select>
        for opener in ("Selecteer", "Kies uw basisverzekering", "Kies je basisverzekering"):
            try:
                page.get_by_text(opener, exact=True).first.click(timeout=3000)
                page.get_by_text(policy, exact=False).first.click(timeout=3000)
                out.append(f"- gekozen via lijst: {policy}")
                break
            except Exception:
                continue
    try:
        page.get_by_role("button", name=re.compile(r"^\s*klaar", re.I)).locator("visible=true").first.click(timeout=3000)
    except Exception:
        pass
    return out


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
        if selector == "-":
            continue
        if not selector:
            lines.append(f"- geen veld voor {value}")
            continue
        try:
            lines.append(f"- {selector}: {fill(page, selector, value)}")
        except Exception as exc:
            lines.append(f"- {selector} ({value}): {type(exc).__name__}: {str(exc)[:150]}")
    try:  # submit inside the finder's own form (the site's header search also says 'Zoeken')
        if submit == "none":
            pass
        elif submit == "enter":
            page.locator(where_sel or what_sel).first.press("Enter", timeout=5000)
        else:
            last = submit.startswith("last:")
            button = page.locator(submit.removeprefix("last:")).locator("visible=true")
            lines.append(f"- zoekknoppen gevonden: {button.count()}")
            (button.last if last else button.first).click(timeout=5000)
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception as exc:
        lines.append(f"- zoeken: {type(exc).__name__}")
    page.wait_for_timeout(5000)
    if name == "cz":  # results come 30 at a time: find how the next ones are asked for
        lines += next_page(page)
        page.wait_for_timeout(5000)
    if name == "zilveren_kruis":  # the finder asks which basic policy you have before it shows statuses
        lines += choose_policy(page, "Basis Zeker")
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
