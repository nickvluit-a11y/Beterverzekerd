"""Beterverzekerd: which hospitals near you are demonstrably better for your procedure?

Format follows the care finders of large insurers: one search bar, a map plus a list of
cards (name, place, distance, one clear label, 2-3 plain-language points), details on click.

Run: streamlit run app/app.py
"""

from __future__ import annotations

import hmac
import re
import os
import sys
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.build_db import connect  # noqa: E402
from pipeline.db_queries import indicator_profile, indicator_trend, latest_judged, locations_for_procedure, quality_latest  # noqa: E402
from pipeline.geo import clean_postcode, locate  # noqa: E402
from pipeline.explain import explain, trend_sentences  # noqa: E402
from pipeline.quality import domain_highlights, domain_of, domain_verdicts  # noqa: E402
from pipeline.reference import labels, procedures, scope  # noqa: E402
from pipeline.score import to_date, attach_organisation, contract_key, contract_for, hospitals_within, latest_waits, load_contracts, load_policies, policy_overview  # noqa: E402

MONTHS_NL = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]


def nice_date(value) -> str:
    """'2026-11-10' -> '10 nov 2026'."""
    try:
        d = pd.Timestamp(value)
        return f"{d.day} {MONTHS_NL[d.month - 1]} {d.year}"
    except (ValueError, TypeError):
        return str(value)


def display_name(row) -> str:
    """'annatommie mc - voor orthopedie - Utrecht' + 'UTRECHT' -> 'Annatommie mc - voor orthopedie - Utrecht'."""
    name = str(row.locatie_naam if isinstance(row.locatie_naam, str) else row.organisatie_naam).strip()
    name = re.sub(r"\s*[-,]?\s*\bconcern\b\s*", " ", name, flags=re.IGNORECASE).strip(" ,-")
    # legal-form and group words mean nothing to a patient
    name = re.sub(r"^stichting\s+", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*\b(b\.?v\.?|n\.?v\.?|groep)(?=\s|$)", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*\|\s*", " · ", name).strip(" ,-·")
    if name[:1].islower():
        name = name[0].upper() + name[1:]
    place = str(row.plaats).strip().title() if isinstance(row.plaats, str) else ""
    return name if not place or place.lower() in name.lower() else f"{name}, {place}"


BADGES = {  # verdict -> (text, css class, map colour)
    "boven_gemiddeld": ("Beter dan gemiddeld", "good", [21, 128, 61]),
    "gemiddeld": ("Geen duidelijk verschil", "avg", [100, 116, 139]),
    "gemengd": ("Deels beter, deels slechter", "mixed", [202, 138, 4]),
    "onder_gemiddeld": ("Slechter dan gemiddeld", "bad", [185, 28, 28]),
    "geen_data": ("Geen vergelijkbare cijfers", "none", [203, 213, 225]),
}
ORDER = list(BADGES)
# Owner's decision: show 'slechter dan gemiddeld' as well. SHOW_WORSE=false switches to the cautious
# variant that only says 'aantoonbaar beter' or 'niet aantoonbaar beter' (both true).
SHOW_WORSE = os.environ.get("SHOW_WORSE", "true").lower() == "true"
if not SHOW_WORSE:
    BADGES = {"boven_gemiddeld": BADGES["boven_gemiddeld"],
              "niet_beter": ("Niet aantoonbaar beter", "avg", [100, 116, 139]),
              "geen_data": BADGES["geen_data"]}
    ORDER = list(BADGES)


def shown_verdict(verdict: str) -> str:
    if SHOW_WORSE or verdict in ("boven_gemiddeld", "geen_data"):
        return verdict
    return "niet_beter"
CONTRACT_CHIP = {"gecontracteerd": ("✓", "ok"), "gecontracteerd_met_plafond": ("✓*", "ok"),
                 "vergoed_als_contract": ("✓", "ok"),
                 "in_onderhandeling": ("…", "wait"), "geen_contract": ("✗", "no")}

st.set_page_config(page_title="Beterverzekerd", page_icon="🩺", layout="centered")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { max-width: 860px; padding-top: 2rem; }
.hero h1 { font-size: 2.1rem; font-weight: 700; color: #0f3d3e; margin-bottom: .2rem; }
.hero p { color: #475569; font-size: 1.05rem; margin-top: 0; }
.card { border: 1px solid #e2e8f0; border-radius: 14px; padding: 16px 18px; margin: 10px 0 4px 0;
        background: #fff; box-shadow: 0 1px 2px rgba(15,23,42,.04); }
.card .top { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
.card .name { font-weight: 600; font-size: 1.05rem; color: #0f172a; }
.card .meta { color: #64748b; font-size: .9rem; }
.badge { display: inline-block; border-radius: 999px; padding: 3px 10px; font-size: .82rem; font-weight: 600; margin: 8px 0 6px 0; }
.badge.good { background: #dcfce7; color: #166534; } .badge.avg { background: #f1f5f9; color: #334155; }
.badge.mixed { background: #fef9c3; color: #854d0e; } .badge.bad { background: #fee2e2; color: #991b1b; }
.badge.none { background: #f8fafc; color: #94a3b8; }
.points { margin: 2px 0 0 0; padding-left: 0; list-style: none; font-size: .93rem; color: #334155; }
.points li.beter::before { content: "▲ "; color: #15803d; } .points li.slechter::before { content: "▼ "; color: #b91c1c; }
.chips { margin-top: 8px; font-size: .8rem; color: #64748b; }
.chip { display: inline-block; border-radius: 6px; padding: 1px 7px; margin: 2px 3px 0 0; border: 1px solid #e2e8f0; }
.chip.ok { background: #f0fdf4; color: #166534; } .chip.no { background: #fef2f2; color: #991b1b; }
.chip.wait { background: #fffbeb; color: #92400e; }
.note { color: #64748b; font-size: .85rem; }
.wait { font-size: .9rem; color: #334155; margin-top: 4px; }
.fact { padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size: .93rem; color: #334155; }
.fact .v { font-size: .85rem; } .fact .v.beter { color: #15803d; } .fact .v.slechter { color: #b91c1c; }
.fact .v.avg { color: #64748b; }
.insurers { margin: 4px 0 14px 0; }
.insurer { display: flex; flex-wrap: wrap; align-items: center; gap: 4px; padding: 8px 12px; border: 1px solid #e2e8f0;
           border-radius: 10px; margin: 6px 0; background: #fff; }
.insurer.mine { border-color: #0f766e; box-shadow: 0 0 0 2px #ccfbf1; }
.insurer .iname { font-weight: 600; min-width: 260px; color: #0f172a; }
.insurer .meta { font-weight: 400; font-size: .82rem; color: #64748b; }
.chip.big { font-size: .9rem; padding: 3px 10px; font-weight: 600; }
.legend { font-size: .8rem; color: #475569; margin: -6px 0 14px 0; display: flex; flex-wrap: wrap; gap: 4px 14px; }
.legend .item { white-space: nowrap; }
.legend .dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; vertical-align: -1px; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def database():
    return connect()


@st.cache_data(ttl=24 * 3600)
def cached_geocode(postcode: str):
    return locate(postcode)


password = os.environ.get("APP_PASSWORD")
if password and not st.session_state.get("authenticated"):
    entered = st.text_input("Wachtwoord", type="password")
    if entered and hmac.compare_digest(entered, password):
        st.session_state["authenticated"] = True
        st.rerun()
    st.caption("Beterverzekerd is nog in ontwikkeling en alleen met wachtwoord te bekijken.")
    st.stop()

con = database()
procs = procedures()

st.markdown('<div class="hero"><h1>Beterverzekerd</h1>'
            '<p>Welk ziekenhuis bij jou in de buurt doet jouw operatie beter dan gemiddeld? '
            'En betaalt jouw zorgverzekering het?</p></div>', unsafe_allow_html=True)

ALL_INSURERS = "Weet ik niet / alle verzekeraars"
NEAR_KM = 30
BRAND = dict(zip(scope()["concern"], scope()["brand"]))  # the name consumers know
LABEL = dict(zip(scope()["concern"], scope()["label"]))  # the policy label whose contracts we show
# every brand of the four groups can be chosen; a brand without own data follows its group's main brand
_BRANDS = labels()[labels()["concern"].isin(scope()["concern"]) & ~labels()["label"].isin(["ONVZ"])]
CONCERN_OF = dict(zip(_BRANDS["label"], _BRANDS["concern"]))
MAIN_BRANDS = list(scope()["label"])
BRAND_CHOICES = MAIN_BRANDS + sorted(set(CONCERN_OF) - set(MAIN_BRANDS), key=str.lower)


def contract_source(row: dict | None) -> str:
    """Where a contract status comes from, with its date: the reader must be able to check it."""
    if not row:
        return ""
    who = ("website van de verzekeraar" if row.get("origin") == "verzekeraar"
           else "website van het ziekenhuis" if row.get("origin") == "ziekenhuis" else "gecontroleerd")
    date = f", {nice_date(row['peildatum'])}" if isinstance(row.get("peildatum"), str) else ""
    plafond = " · let op: dit ziekenhuis kan voor deze verzekeraar vol raken; vraag of er plek is" \
        if str(row.get("omzetplafond")).lower() == "true" or row.get("status") == "gecontracteerd_met_plafond" else ""
    budget = " · geldt voor de gewone polis; bij een budgetpolis kan het anders zijn" if row.get("origin") == "verzekeraar" else ""
    return f'<div class="note">Bron: {who}{date}{plafond}{budget}</div>'


with st.form("zoek", border=False):
    c1, c2, c3 = st.columns([1.2, 1.6, 1])
    postcode = c1.text_input("Jouw postcode", value="3584 CX")
    proc_name = c2.selectbox("Welke operatie?", procs["name_nl"].tolist())
    radius = c3.selectbox("Hoe ver wil je reizen?", [10, 25, 50, 100], index=1, format_func=lambda km: f"tot {km} km")
    insurer = st.selectbox("Bij wie ben je verzekerd?", [ALL_INSURERS] + BRAND_CHOICES,
                           format_func=lambda b: b if b in (ALL_INSURERS, *MAIN_BRANDS)
                           else f"{b} (onderdeel van {BRAND.get(CONCERN_OF[b], CONCERN_OF[b])})")
    submitted = st.form_submit_button("Laat zien", type="primary", width="stretch")

if submitted:
    code = clean_postcode(postcode)
    try:
        coords = cached_geocode(code) if code else None
    except Exception:
        coords = None
    if not code or not coords:
        st.session_state.pop("search", None)
        st.error("Deze postcode konden we niet vinden. Probeer bijvoorbeeld 3584 CX.")
    else:
        st.session_state["search"] = {"coords": coords, "radius": radius, "proc_name": proc_name, "insurer": insurer,
                                      "procedure_id": procs.loc[procs["name_nl"] == proc_name, "procedure_id"].iloc[0]}

search = st.session_state.get("search")
if search:
    proc = search["procedure_id"]
    near = hospitals_within(*search["coords"], search["radius"], locations_for_procedure(con, proc))
    verdicts = quality_latest(con, proc)[["location_key", "quality_verdict", "verslagjaar", "volume"]]
    near = near.merge(verdicts, on="location_key", how="left")
    waits = latest_waits(proc).rename(columns={"weeks": "wait_weeks", "peildatum": "wait_date"})
    near = near.merge(waits[["location_key", "wait_weeks", "wait_type", "wait_date"]], on="location_key", how="left")
    near["quality_verdict"] = near["quality_verdict"].fillna("geen_data").map(shown_verdict)
    near["_order"] = near["quality_verdict"].map(ORDER.index)
    near["display_name"] = [display_name(r) for r in near.itertuples()]
    # within 30 km the better hospitals first; further away only after those (a far 'better' one
    # should not push the hospital next door out of sight)
    near["_far"] = near["distance_km"] > NEAR_KM
    near = near.sort_values(["_far", "_order", "distance_km"]).reset_index(drop=True)
    judged = latest_judged(con, proc)
    contracts = attach_organisation(load_contracts())
    concerns = list(scope()["concern"])

    if near.empty:
        st.info(f"Geen ziekenhuizen binnen {search['radius']} km die deze ingreep uitvoeren. Kies een grotere afstand.")
    else:
        counts = near["quality_verdict"].value_counts()
        n_good = int(counts.get("boven_gemiddeld", 0))
        st.markdown(f"**{len(near)} {'ziekenhuis doet' if len(near) == 1 else 'ziekenhuizen doen'}** deze operatie "
                    f"binnen {search['radius']} km. "
                    + (f"**{n_good}** daarvan {'scoort' if n_good == 1 else 'scoren'} beter dan gemiddeld."
                       if n_good else "Geen daarvan scoort aantoonbaar beter dan gemiddeld; kies eventueel een grotere afstand."))

        points = near.assign(color=near["quality_verdict"].map(lambda v: BADGES[v][2]),
                             label=near["display_name"] + " · " + near["quality_verdict"].map(lambda v: BADGES[v][0]))
        you = pd.DataFrame([{"lat": search["coords"][0], "lon": search["coords"][1]}])
        st.pydeck_chart(pdk.Deck(
            map_style="light",
            initial_view_state=pdk.ViewState(latitude=search["coords"][0], longitude=search["coords"][1],
                                             zoom=11 if search["radius"] <= 10 else 9 if search["radius"] <= 25 else 8),
            layers=[pdk.Layer("ScatterplotLayer", points, get_position="[lon, lat]", get_fill_color="color",
                              get_radius=900, radius_min_pixels=6, pickable=True),
                    pdk.Layer("ScatterplotLayer", you, get_position="[lon, lat]", get_fill_color=[15, 61, 62],
                              get_radius=400, radius_min_pixels=5)],
            tooltip={"text": "{label}"}), height=320)
        shown_kinds = [v for v in ORDER if v in set(near["quality_verdict"])]
        legend = "".join(f'<span class="item"><span class="dot" style="background:rgb({",".join(map(str, BADGES[v][2]))})">'
                         f'</span>{BADGES[v][0]}</span>' for v in shown_kinds)
        st.markdown(f'<div class="legend">{legend}<span class="item"><span class="dot" style="background:#0f3d3e"></span>'
                    'Waar jij woont</span></div>',
                    unsafe_allow_html=True)

        chosen = search.get("insurer", ALL_INSURERS)
        if chosen != ALL_INSURERS and chosen not in CONCERN_OF:  # a stale session value
            chosen = ALL_INSURERS
        chosen_concern = CONCERN_OF.get(chosen)
        main_brand = LABEL.get(chosen_concern, chosen)
        has_contracts = not contracts.empty

        def render_policies() -> None:
            """Compare policies on access to the better hospitals in reach (quality first, then price)."""
            n_better = int(counts.get("boven_gemiddeld", 0))
            if not n_better:
                return
            policies = load_policies(2027)
            if chosen != ALL_INSURERS:
                policies = policies[policies["label"] == chosen]
                if policies.empty:
                    st.markdown(f"#### Kun je met {chosen} naar de betere ziekenhuizen?")
                    st.caption(f"Premies en polissen van {chosen} tonen we nog niet. Bij de ziekenhuizen hieronder zie je "
                               f"de contracten van {main_brand}; die gelden meestal ook voor {chosen}, maar check je polis.")
                    return
            table = policy_overview(near, contracts, policies)
            what = "het betere ziekenhuis" if n_better == 1 else f"de {n_better} betere ziekenhuizen"
            whose = "" if chosen == ALL_INSURERS else f" van {chosen}"
            st.markdown(f"#### Welke polis{whose} betaalt {what}?")

            def policy_row(r) -> str:
                premie = f"€ {r.premie:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " p/m" \
                    if pd.notna(r.premie) else "premie onbekend"
                pct = pd.to_numeric(r.vergoeding_niet_gecontracteerd_pct, errors="coerce")
                kind = " · je mag naar elk ziekenhuis*" if pd.notna(pct) and pct >= 100 else ""
                n = r.betere_ziekenhuizen
                of = (lambda k: "" if n == 1 else f"{k} van {n} ")
                parts = [f'<span class="chip ok">✓ {of(r.volledig + r.vrij)}betaald</span>' if r.volledig + r.vrij else "",
                         f'<span class="chip no">€ {of(r.deels)}deels zelf betalen</span>' if r.deels else "",
                         f'<span class="chip">? {of(r.onbekend)}nog niet bekend</span>' if r.onbekend else ""]
                conf = getattr(r, "confirmed", None)
                checked = (" · premie nog niet bevestigd door de verzekeraar"
                           if conf is not None and not pd.isna(conf) and not conf else "")
                return (f'<div class="insurer"><span class="iname">{r.label} – {r.polis}'
                        f'<br><span class="meta">{premie}{kind}{checked}</span></span>{"".join(parts)}</div>')

            st.markdown('<div class="insurers">' + "".join(policy_row(r) for r in table.head(8).itertuples()) + "</div>",
                        unsafe_allow_html=True)
            if len(table) > 8:
                with st.expander(f"Toon alle {len(table)} polissen"):
                    st.markdown('<div class="insurers">' + "".join(policy_row(r) for r in table.iloc[8:].itertuples())
                                + "</div>", unsafe_allow_html=True)
            notes = []
            if table["vrij"].sum():
                notes.append("* Deze polis betaalt ook ziekenhuizen zonder contract, tot het normale tarief. "
                             "Rekent een ziekenhuis meer, dan betaal je het verschil zelf.")
            if (table["polis_type"].astype(str) == "budget").any():
                notes.append("Bij budgetpolissen (de goedkoopste) hebben verzekeraars vaak met minder ziekenhuizen "
                             "een contract. De zorgzoekers tonen dat nog niet per polis, dus daar staat '?'. "
                             "Check het bij je verzekeraar voordat je zo'n polis kiest.")
            unknown_share = table["onbekend"].sum() / max(1, table["betere_ziekenhuizen"].sum())
            if unknown_share > 0.3:
                notes.append("? = nog niet bekend. Verzekeraars en ziekenhuizen maken hun afspraken voor 2027 "
                             "tussen november en januari. We werken dit bij zodra zij het publiceren.")
            for note in notes:
                st.caption(note)

        def render_card(row) -> None:
            text, css, _ = BADGES[row.quality_verdict]
            points_html = "".join(f'<li class="{v}">{s}</li>' for v, s in
                                  domain_highlights(judged[judged["location_key"] == row.location_key])
                                  if SHOW_WORSE or v == "beter")
            year = f" · cijfers {int(row.verslagjaar)}" if pd.notna(row.verslagjaar) else ""
            if pd.notna(row.wait_weeks):
                what = "operatie" if row.wait_type == "behandeling" else "eerste afspraak"
                weeks = max(1, round(float(row.wait_weeks)))
                old = (pd.Timestamp.now() - pd.Timestamp(row.wait_date)).days > 120 if pd.notna(row.wait_date) else False
                wait_html = (f'<div class="wait">⏱ Wachttijd {what}: ± {weeks} {"week" if weeks == 1 else "weken"}'
                             f'<span class="note"> · NZa, {nice_date(row.wait_date)}{" (oude meting)" if old else ""}'
                             '</span></div>')
            else:
                wait_html = ""
            key = contract_key(row.organisatie_agb, row.location_key)
            found = {c: contract_for(contracts, key, c, LABEL.get(c, c)) for c in concerns} if has_contracts else {}
            found = {c: r for c, r in found.items() if r}
            if chosen != ALL_INSURERS:
                own = contract_for(contracts, key, chosen_concern, chosen) if has_contracts else None
                own = own if own and own.get("label") == chosen else None  # the brand's own row, not concern-wide
                mine = own or found.get(chosen_concern)
                status = (mine or {}).get("status")
                mark, chip_css = CONTRACT_CHIP.get(status, ("?", ""))
                label = {"gecontracteerd": "betaald, er is een contract", "gecontracteerd_met_plafond": "betaald, er is een contract",
                         "vergoed_als_contract": "betaald, afspraken nog niet rond",
                         "in_onderhandeling": "nog in gesprek: misschien betaal je een deel zelf",
                         "geen_contract": "geen contract: misschien betaal je een deel zelf"}.get(status, "nog niet bekend")
                via = ("" if own or chosen == main_brand or not mine
                       else f'<div class="note">Contract van {main_brand}; geldt meestal ook voor {chosen}, check je polis.</div>')
                chips_html = (f'<div class="chips"><span class="chip big {chip_css}">{chosen}: {mark} {label}</span>'
                              f'{contract_source(mine)}{via}</div>')
            elif found:
                chips = []
                for concern in concerns:
                    mark, chip_css = CONTRACT_CHIP.get((found.get(concern) or {}).get("status"), ("?", ""))
                    chips.append(f'<span class="chip {chip_css}">{BRAND.get(concern, concern)} {mark}</span>')
                origins = sorted({str(r.get("origin") or "ziekenhuis") for r in found.values()})
                source = "Contracten 2027 volgens " + " en ".join(
                    {"verzekeraar": "de verzekeraar", "ziekenhuis": "het ziekenhuis"}[o]
                    for o in origins) + " · ✓ betaald · … nog in gesprek · ✗ geen contract · ? nog niet bekend"
                chips_html = ('<div class="chips">' + "".join(chips) + f'<div class="note">{source}</div></div>')
            else:
                chips_html = '<div class="chips">Contracten 2027 voor dit ziekenhuis: nog niet bekend</div>'
            st.markdown(
                f'<div class="card"><div class="top"><span class="name">{row.display_name}</span>'
                f'<span class="meta">{row.distance_km:.0f} km{year}</span></div>'
                f'<span class="badge {css}">{text}</span>'
                f'<ul class="points">{points_html}</ul>{wait_html}{chips_html}</div>', unsafe_allow_html=True)
            with st.expander("Waarom dit oordeel?"):
                render_details(row)

        def render_details(row) -> None:
            profile = indicator_profile(con, row.location_key, proc)
            shown = profile[profile["verdict"].isin(["beter", "slechter", "gemiddeld"])]
            if shown.empty:
                st.caption("Voor dit ziekenhuis zijn geen cijfers waar we een betrouwbare uitspraak over kunnen doen.")
            else:
                # the card's verdict per domain decides; a single patient question cannot overrule it
                domains = domain_verdicts(shown.assign(indicator_nl=shown["indicator"]))
                groups: dict[str, list[str]] = {}
                for r in shown.to_dict("records"):
                    title, measured, (css, verdict) = explain(r)
                    domain = domain_of(r["indicator"])
                    if css in ("beter", "slechter") and domain and domains.get(domain) not in (css,):
                        css, verdict = "avg", ("op deze vraag " + ("hoger" if css == "beter" else "lager")
                                               + ", maar de andere vragen bevestigen dat niet")
                    if not SHOW_WORSE and css == "slechter":
                        css, verdict = "avg", "niet duidelijk beter"
                    n = pd.to_numeric(r.get("denominator"), errors="coerce")
                    size = f" · {int(n):,} patiënten".replace(",", ".") if pd.notna(n) and n > 0 else ""
                    groups.setdefault(title, []).append(f'{measured}{size} · <span class="v {css}">{verdict}</span>')
                lines = [f'<div class="fact"><b>{title}</b><br>' + "<br>".join(items) + "</div>"
                         for title, items in groups.items()]
                unjudged = profile[profile["indicator"].astype(str).str.startswith("Verbetering volgens patiënt na 12")
                                   & profile["verdict"].isna() & profile["position"].notna()]
                if not unjudged.empty and "Herstel volgens patiënten" not in groups:
                    reason = str(unjudged["position"].iloc[0])
                    why = ("te weinig patiënten vulden de vragenlijst in" if "respons" in reason or "patiënten" in reason
                           else "de cijfers in de bron kloppen niet")
                    lines.append(f'<div class="fact"><b>Herstel volgens patiënten</b><br>'
                                 f'<span class="v avg">geen oordeel: {why}</span></div>')
                year = int(shown["verslagjaar"].max())
                st.markdown("".join(lines) + f'<p class="note">Cijfers over {year}, bron: Zorginstituut Nederland. '
                            'Bij kleine aantallen patiënten kan een verschil toeval zijn; dan zeggen we '
                            '"niet duidelijk anders".</p>', unsafe_allow_html=True)
                # a trend only for indicators that are also in this year's figures
                trend = indicator_trend(con, row.location_key, proc)
                if not trend.empty:
                    last = trend.groupby("indicator")["verslagjaar"].transform("max")
                    trend = trend[(last == year) & trend["indicator"].isin(shown["indicator"])]
                sentences = trend_sentences(trend)
                if not SHOW_WORSE:
                    sentences = [s for s in sentences if "slechter" not in s]
                for sentence in sentences:
                    st.markdown(f"📈 {sentence}")
            if pd.notna(row.volume):
                st.caption(f"{int(row.volume)} van deze operaties per jaar op deze locatie.")

        # quality first: the best nearby hospitals, then which policy covers them, then the rest
        st.markdown("#### Ziekenhuizen")
        for row in near.head(3).itertuples():
            render_card(row)
        render_policies()
        if len(near) > 3:
            st.markdown(f"#### Meer ziekenhuizen binnen {search['radius']} km")
            for row in near.iloc[3:].itertuples():
                render_card(row)

st.divider()
if search:
    freshness = [f"kwaliteit: Zorginstituut, cijfers over {int(near['verslagjaar'].max())}"] if not near.empty and near["verslagjaar"].notna().any() else []
    if not near.empty and near["wait_date"].notna().any():
        freshness.append(f"wachttijden: NZa, {nice_date(near['wait_date'].dropna().max())}")
    dates = contracts["peildatum"].map(to_date).dropna() if not contracts.empty and "peildatum" in contracts else []
    if len(dates):
        freshness.append(f"contracten: verzekeraars en ziekenhuizen, laatst bijgewerkt {nice_date(dates.max())}")
    if freshness:
        st.caption("Bronnen · " + " · ".join(freshness))
st.markdown(
    '<p class="note"><b>Hoe werkt het?</b> Elk ziekenhuis moet elk jaar aan de overheid laten weten hoe het gaat: '
    'hoe vaak een operatie over moet, hoe vaak er een infectie komt en hoe patiënten zich voelen na de operatie. '
    'Wij vergelijken die cijfers met alle andere ziekenhuizen.<br>'
    '<b>Beter dan gemiddeld</b>: op een belangrijk punt duidelijk beter, en nergens slechter. '
    '<b>Slechter dan gemiddeld</b>: alleen als het verschil heel duidelijk is. '
    '<b>Geen duidelijk verschil</b>: niet duidelijk anders, of te weinig patiënten om het zeker te weten. '
    'Academische ziekenhuizen helpen vaker zieke patiënten; dat telt niet mee in de cijfers.<br>'
    'Dit is geen medisch advies. Vraag je huisarts en je verzekeraar of je ergens terecht kunt.</p>',
    unsafe_allow_html=True)
