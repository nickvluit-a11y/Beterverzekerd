"""Beterverzekerd prototype: compare health-insurance policies on the QUALITY of contracted care.

Run: streamlit run app/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.build_db import connect  # noqa: E402
from pipeline.db_queries import has_quality_data, indicator_profile, indicator_trend  # noqa: E402
from pipeline.geo import clean_postcode, geocode_postcode  # noqa: E402
from pipeline.reference import MANUAL, procedures  # noqa: E402
from pipeline.score import overview  # noqa: E402

ACCESS_LABELS = {
    "gecontracteerd": "✅ Gecontracteerd",
    "gecontracteerd_met_plafond": "⚠️ Gecontracteerd, met omzetplafond",
    "vrije_keuze": "🔓 Vrije keuze (restitutie, tot marktconform tarief)",
    "in_onderhandeling": "⏳ In onderhandeling",
    "geen_contract": "❌ Geen contract",
    "onbekend": "❔ Contract onbekend",
}
QUALITY_LABELS = {
    "boven_gemiddeld": "🟢 Boven landelijk gemiddelde",
    "gemiddeld": "⚪ Rond landelijk gemiddelde",
    "gemengd": "🟡 Gemengd (deels beter, deels slechter)",
    "onder_gemiddeld": "🔴 Onder landelijk gemiddelde",
    "geen_data": "❔ Geen beoordeelbare uitkomstdata",
}
VERDICT_LABELS = {"beter": "🟢 beter", "slechter": "🔴 slechter", "gemiddeld": "⚪ rond gemiddelde"}

st.set_page_config(page_title="Beterverzekerd", page_icon="🏥", layout="wide")
st.title("Beterverzekerd")
st.caption("Vergelijk zorgpolissen op de kwaliteit van de ziekenhuizen die ze voor jou inkopen, niet alleen op prijs.")
st.warning(
    "**Prototype.** Geen medisch of financieel advies. Contractstatus is geen garantie op toegang "
    "(omzetplafonds, vergoeding tijdens onderhandelingen). Controleer altijd bij je verzekeraar."
)


@st.cache_resource
def database():
    return connect()


@st.cache_data(ttl=24 * 3600)
def cached_geocode(postcode: str):
    return geocode_postcode(postcode)


con = database()
procs = procedures()

with st.form("zoek"):
    col1, col2, col3 = st.columns([2, 2, 1])
    postcode = col1.text_input("Postcode", value="3584 CX")
    proc_name = col2.selectbox("Ingreep", procs["name_nl"].tolist())
    radius = col3.number_input("Straal (km)", min_value=5, max_value=150, value=25, step=5)
    submitted = st.form_submit_button("Vergelijk polissen")

if submitted:
    code = clean_postcode(postcode)
    coords = None
    if code:
        try:
            coords = cached_geocode(code)
        except Exception:
            coords = None
    if not code:
        st.session_state.pop("result", None)
        st.error("Vul een geldige postcode in, bijvoorbeeld 3584 CX.")
    elif not coords:
        st.session_state.pop("result", None)
        st.error("Kon deze postcode niet vinden (PDOK Locatieserver).")
    else:
        procedure_id = procs.loc[procs["name_nl"] == proc_name, "procedure_id"].iloc[0]
        summary, detail = overview(coords[0], coords[1], procedure_id, radius_km=radius, con=con)
        st.session_state["result"] = {"summary": summary, "detail": detail, "radius": radius,
                                      "procedure_id": procedure_id, "proc_name": proc_name}

result = st.session_state.get("result")
if result:
    summary, detail = result["summary"], result["detail"]
    if detail.empty:
        st.info(f"Geen ziekenhuizen binnen {result['radius']} km die deze ingreep uitvoeren.")
    else:
        if not has_quality_data(con):
            st.info("Er is nog geen kwaliteitsdata geladen.")
        contracts_file = MANUAL / "contracts.csv"
        if not contracts_file.exists() or pd.read_csv(contracts_file).empty:
            st.info("Contractstatus is nog niet gecontroleerd ingevoerd; kwaliteit telt daarom nog alleen mee "
                    "bij restitutiepolissen. Per ziekenhuis zie je de kwaliteit wel al in het tweede tabblad.")
        tab_policies, tab_hospitals = st.tabs(["Polissen vergelijken op kwaliteit", "Kwaliteit per ziekenhuis"])

        with tab_policies:
            per_hospital = detail.drop_duplicates("location_key")["quality"].value_counts()
            st.markdown(
                f"**{detail['location_key'].nunique()} ziekenhuislocaties binnen {result['radius']} km** voeren deze ingreep uit: "
                f"🟢 {per_hospital.get('boven_gemiddeld', 0)} boven gemiddeld · ⚪ {per_hospital.get('gemiddeld', 0)} rond gemiddeld · "
                f"🟡 {per_hospital.get('gemengd', 0)} gemengd · 🔴 {per_hospital.get('onder_gemiddeld', 0)} onder gemiddeld. "
                "De vraag per polis: welke daarvan krijg je volledig vergoed?")
            order = ["label", "polis", "kwaliteit_boven_gemiddeld", "kwaliteit_gemengd", "kwaliteit_onder_gemiddeld",
                     "kwaliteit_geen_data", "boven_gemiddeld_contract_onbekend", "premie_per_maand", "polis_type", "kortste_wachttijd_weken",
                     "ziekenhuizen_in_bereik", "gecontracteerd", "met_omzetplafond", "vrije_keuze",
                     "in_onderhandeling", "geen_contract", "onbekend", "concern"]
            ranked = summary.sort_values(["kwaliteit_boven_gemiddeld", "kwaliteit_onder_gemiddeld"], ascending=[False, True])
            st.dataframe(ranked[[c for c in order if c in ranked]].dropna(axis=1, how="all").rename(columns={
                "kwaliteit_boven_gemiddeld": "🟢 Boven gemiddeld", "kwaliteit_gemengd": "🟡 Gemengd",
                "kwaliteit_onder_gemiddeld": "🔴 Onder gemiddeld", "kwaliteit_geen_data": "❔ Geen kwaliteitsdata",
                "boven_gemiddeld_contract_onbekend": "🟢 Boven gemiddeld, contract onbekend",
                "concern": "Concern", "label": "Label", "polis": "Polis", "polis_type": "Type",
                "premie_per_maand": "Premie p/m (€)", "ziekenhuizen_in_bereik": "Ziekenhuizen in bereik",
                "gecontracteerd": "Gecontracteerd", "met_omzetplafond": "Met plafond",
                "vrije_keuze": "Vrije keuze", "in_onderhandeling": "In onderhandeling",
                "geen_contract": "Geen contract", "onbekend": "Contract onbekend",
                "kortste_wachttijd_weken": "Kortste wachttijd (wk)",
            }), hide_index=True, use_container_width=True)
            st.caption(
                "Kwaliteitskolommen tellen ziekenhuizen binnen bereik die je met deze polis volledig vergoed krijgt "
                "(gecontracteerd of restitutie). 'Boven gemiddeld': op minstens één openbare uitkomstindicator "
                "aantoonbaar beter dan het landelijk gemiddelde (95%-betrouwbaarheidsinterval) en op geen enkele slechter. "
                "Kleine ziekenhuizen staan vaak op 'rond gemiddeld': een verschil is dan niet aan te tonen.")
            chosen = st.selectbox("Details voor polis", summary["naam"].tolist())
            rows = detail[detail["naam"] == chosen].copy()
            rows["access"] = rows["access"].map(ACCESS_LABELS)
            rows["quality"] = rows["quality"].map(QUALITY_LABELS)
            cols = ["location", "quality", "quality_better", "quality_worse", "quality_year", "volume",
                    "access", "wait_weeks", "distance_km", "contract_peildatum", "contract_source"]
            st.dataframe(rows[cols].dropna(axis=1, how="all").rename(columns={
                "location": "Ziekenhuis", "quality": "Kwaliteit", "quality_better": "Indicatoren beter",
                "quality_worse": "Indicatoren slechter", "quality_year": "Verslagjaar", "volume": "Aantal ingrepen",
                "access": "Contract", "wait_weeks": "Wachttijd (wk)", "distance_km": "Afstand (km)",
                "contract_peildatum": "Peildatum contract", "contract_source": "Bron contract",
            }), hide_index=True, use_container_width=True)

        with tab_hospitals:
            hospitals_near = (detail.drop_duplicates("location_key")
                              .sort_values(["quality", "distance_km"])[["location_key", "location", "quality", "distance_km"]])
            label_for = {r.location_key: f"{r.location} · {QUALITY_LABELS.get(r.quality, r.quality)} · {r.distance_km} km"
                         for r in hospitals_near.itertuples()}
            key = st.selectbox("Ziekenhuis", list(label_for), format_func=label_for.get)
            profile = indicator_profile(con, key, result["procedure_id"])
            if profile.empty:
                st.info("Geen indicatoren gevonden voor dit ziekenhuis.")
            else:
                year = int(profile["verslagjaar"].max())
                st.markdown(f"**{result['proc_name']}: openbare indicatoren, verslagjaar {year}** (bron: Zorginzicht)")
                judged = profile[profile["method"].notna()].copy()
                if not judged.empty:
                    pct = judged["method"] == "ratio"
                    for col in ["rate", "ci_low", "ci_high", "national_rate"]:
                        judged.loc[pct, col] = judged.loc[pct, col] * 100
                    judged["Oordeel"] = judged["verdict"].map(VERDICT_LABELS).fillna(
                        judged["position"].map({"gunstiger": "gunstiger dan gemiddeld (geen oordeel)",
                                                "ongunstiger": "ongunstiger dan gemiddeld (geen oordeel)",
                                                "gelijk": "gelijk aan gemiddelde"}))
                    st.dataframe(judged[["indicator", "rate", "ci_low", "ci_high", "national_rate", "Oordeel", "denominator"]]
                                 .rename(columns={"indicator": "Indicator", "rate": "Ziekenhuis", "ci_low": "95% laag",
                                                  "ci_high": "95% hoog", "national_rate": "Landelijk",
                                                  "denominator": "Aantal patiënten"}).round(2),
                                 hide_index=True, use_container_width=True)
                other = profile[profile["method"].isna()]
                if not other.empty:
                    with st.expander(f"Overige indicatoren ({len(other)}): volume, proces, structuur (geen oordeel)"):
                        st.dataframe(other[["indicator_naam", "indicator_type", "eenheid", "value"]].rename(columns={
                            "indicator_naam": "Indicator", "indicator_type": "Type", "eenheid": "Eenheid", "value": "Waarde"}),
                            hide_index=True, use_container_width=True)
                trend = indicator_trend(con, key, result["procedure_id"])
                if trend["verslagjaar"].nunique() > 1:
                    st.markdown("**Verloop over de jaren** (ziekenhuis tegenover landelijk)")
                    for indicator, group in trend.groupby("indicator"):
                        chart = group.set_index("verslagjaar")[["rate", "national_rate"]].rename(
                            columns={"rate": "Ziekenhuis", "national_rate": "Landelijk"})
                        if group["method"].iloc[0] == "ratio":
                            chart = chart * 100
                        st.caption(indicator)
                        st.line_chart(chart, height=180)

with st.expander("Over de data en de methode"):
    st.markdown(
        "- **Kwaliteit:** openbare indicatoren van Zorginstituut Nederland (Zorginzicht), per ziekenhuislocatie, "
        "verslagjaren 2022–2025. Een ziekenhuis is alleen 'beter' of 'slechter' als het 95%-betrouwbaarheidsinterval "
        "het landelijk gemiddelde niet raakt. PROM-scores (wat patiënten zelf rapporteren) tonen we naast het landelijk "
        "gemiddelde zonder oordeel, omdat de spreiding per ziekenhuis niet openbaar is.\n"
        "- **Ziekenhuizen in bereik:** alle locaties die deze ingreep aantoonbaar uitvoeren (ze rapporteren indicatoren).\n"
        "- **Contracten:** per ziekenhuisorganisatie, uit de eigen publicaties van ziekenhuizen; eerst met de hand gecontroleerd.\n"
        "- **Locaties:** PDOK. **Wachttijden:** NZa (nog niet beschikbaar).\n"
        "- We tonen bewust geen ranglijst van ziekenhuizen: kleine aantallen en verschillen in patiëntengroepen maken die misleidend."
    )
