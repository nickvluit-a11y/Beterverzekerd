"""Beterverzekerd: which hospitals near you are demonstrably better for your procedure?

Format follows the care finders of large insurers: one search bar, a map plus a list of
cards (name, place, distance, one clear label, 2-3 plain-language points), details on click.

Run: streamlit run app/app.py
"""

from __future__ import annotations

import hmac
import os
import sys
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.build_db import connect  # noqa: E402
from pipeline.db_queries import indicator_profile, indicator_trend, latest_judged, locations_for_procedure, quality_latest  # noqa: E402
from pipeline.geo import clean_postcode, geocode_postcode  # noqa: E402
from pipeline.quality import domain_highlights  # noqa: E402
from pipeline.reference import labels, procedures  # noqa: E402
from pipeline.score import attach_organisation, contract_for, hospitals_within, load_contracts  # noqa: E402

def display_name(row) -> str:
    """'annatommie mc - voor orthopedie - Utrecht' + 'UTRECHT' -> 'Annatommie mc - voor orthopedie - Utrecht'."""
    name = str(row.locatie_naam if isinstance(row.locatie_naam, str) else row.organisatie_naam).strip()
    if name[:1].islower():
        name = name[0].upper() + name[1:]
    place = str(row.plaats).strip().title() if isinstance(row.plaats, str) else ""
    return name if not place or place.lower() in name.lower() else f"{name}, {place}"


BADGES = {  # verdict -> (text, css class, map colour)
    "boven_gemiddeld": ("Beter dan gemiddeld", "good", [21, 128, 61]),
    "gemiddeld": ("Rond het gemiddelde", "avg", [100, 116, 139]),
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
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def database():
    return connect()


@st.cache_data(ttl=24 * 3600)
def cached_geocode(postcode: str):
    return geocode_postcode(postcode)


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
            '<p>Welke ziekenhuizen bij jou in de buurt zijn aantoonbaar beter voor jouw ingreep, '
            'en kun je daar terecht met je zorgverzekering?</p></div>', unsafe_allow_html=True)

with st.form("zoek", border=False):
    c1, c2, c3 = st.columns([1.2, 1.6, 1])
    postcode = c1.text_input("Postcode", value="3584 CX")
    proc_name = c2.selectbox("Ingreep", procs["name_nl"].tolist())
    radius = c3.selectbox("Afstand", [10, 25, 50, 100], index=1, format_func=lambda km: f"{km} km")
    submitted = st.form_submit_button("Zoek ziekenhuizen", type="primary", width="stretch")

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
        st.session_state["search"] = {"coords": coords, "radius": radius, "proc_name": proc_name,
                                      "procedure_id": procs.loc[procs["name_nl"] == proc_name, "procedure_id"].iloc[0]}

search = st.session_state.get("search")
if search:
    proc = search["procedure_id"]
    near = hospitals_within(*search["coords"], search["radius"], locations_for_procedure(con, proc))
    verdicts = quality_latest(con, proc)[["location_key", "quality_verdict", "verslagjaar", "volume"]]
    near = near.merge(verdicts, on="location_key", how="left")
    near["quality_verdict"] = near["quality_verdict"].fillna("geen_data").map(shown_verdict)
    near["_order"] = near["quality_verdict"].map(ORDER.index)
    near["display_name"] = [display_name(r) for r in near.itertuples()]
    near = near.sort_values(["_order", "distance_km"]).reset_index(drop=True)
    judged = latest_judged(con, proc)
    contracts = attach_organisation(load_contracts())
    concerns = list(dict.fromkeys(labels()["concern"]))

    if near.empty:
        st.info(f"Geen ziekenhuizen binnen {search['radius']} km die deze ingreep uitvoeren. Kies een grotere afstand.")
    else:
        counts = near["quality_verdict"].value_counts()
        st.markdown(f"**{len(near)} ziekenhuizen** binnen {search['radius']} km doen een {search['proc_name'].lower()}. "
                    f"**{counts.get('boven_gemiddeld', 0)}** daarvan scoren aantoonbaar beter dan gemiddeld.")

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

        has_contracts = not contracts.empty
        for row in near.itertuples():
            text, css, _ = BADGES[row.quality_verdict]
            points_html = "".join(f'<li class="{v}">{s}</li>' for v, s in
                                  domain_highlights(judged[judged["location_key"] == row.location_key])
                                  if SHOW_WORSE or v == "beter")
            year = f" · cijfers {int(row.verslagjaar)}" if pd.notna(row.verslagjaar) else ""
            found = {c: contract_for(contracts, row.organisatie_agb, c, c) for c in concerns} if has_contracts else {}
            found = {c: r for c, r in found.items() if r}
            if found:
                chips = []
                for concern in concerns:
                    mark, chip_css = CONTRACT_CHIP.get((found.get(concern) or {}).get("status"), ("?", ""))
                    chips.append(f'<span class="chip {chip_css}">{concern} {mark}</span>')
                first = next(iter(found.values()))
                auto = any(not r.get("checked", True) for r in found.values())
                peildatum = f" · peildatum {first.get('peildatum')}" if isinstance(first.get("peildatum"), str) else ""
                source = ("Contracten 2027 volgens de website van het ziekenhuis" + peildatum +
                          (" · automatisch uitgelezen, controleer bij je verzekeraar" if auto else ""))
                chips_html = ('<div class="chips">' + "".join(chips) + f'<div class="note">{source}</div></div>')
            else:
                chips_html = '<div class="chips">Contracten 2027 voor dit ziekenhuis: nog niet bekend</div>'
            st.markdown(
                f'<div class="card"><div class="top"><span class="name">{row.display_name}</span>'
                f'<span class="meta">{row.distance_km:.0f} km{year}</span></div>'
                f'<span class="badge {css}">{text}</span>'
                f'<ul class="points">{points_html}</ul>{chips_html}</div>', unsafe_allow_html=True)
            with st.expander("Bekijk de cijfers"):
                profile = indicator_profile(con, row.location_key, proc)
                shown = profile[profile["verdict"].isin(["beter", "slechter", "gemiddeld"])].copy()
                if shown.empty:
                    st.caption("Geen indicatoren met een betrouwbaar oordeel voor dit ziekenhuis.")
                else:
                    ratio = shown["method"] == "ratio"
                    for col in ["rate", "national_rate"]:
                        shown.loc[ratio, col] = shown.loc[ratio, col] * 100
                    if not SHOW_WORSE:
                        shown["verdict"] = shown["verdict"].map({"beter": "beter"}).fillna("niet aantoonbaar beter")
                    st.dataframe(shown[["indicator", "rate", "national_rate", "verdict"]].rename(columns={
                        "indicator": "Indicator", "rate": "Dit ziekenhuis", "national_rate": "Landelijk",
                        "verdict": "Oordeel"}).round(2), hide_index=True, width="stretch")
                trend = indicator_trend(con, row.location_key, proc)
                if trend["verslagjaar"].nunique() > 1:
                    trend = trend[trend["verdict"].notna()].copy()
                    if not SHOW_WORSE:
                        trend["verdict"] = trend["verdict"].map({"beter": "beter"}).fillna("niet aantoonbaar beter")
                    pivot = trend.pivot_table(
                        index="verslagjaar", columns="indicator", values="verdict", aggfunc="first")
                    st.caption("Oordeel per jaar")
                    st.dataframe(pivot, width="stretch")
                if pd.notna(row.volume):
                    st.caption(f"{int(row.volume)} ingrepen per jaar op deze locatie.")

st.divider()
st.markdown(
    '<p class="note"><b>Hoe we kwaliteit beoordelen.</b> We gebruiken de openbare kwaliteitscijfers van Zorginstituut '
    'Nederland (Zorginzicht). Een ziekenhuis is alleen "beter" of "slechter" als het verschil met het landelijk niveau '
    'groter is dan de gebruikelijke spreiding tussen ziekenhuizen. Kleine verschillen tellen niet. Alleen heroperaties '
    'zijn gecorrigeerd voor patiëntkenmerken; academische centra behandelen vaker complexe patiënten. '
    'Geen ranglijst, geen medisch of financieel advies. Contractstatus is geen garantie op toegang.</p>',
    unsafe_allow_html=True)
