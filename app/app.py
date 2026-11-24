"""Beterverzekerd prototype: postcode + procedure -> overview per policy.

Run: streamlit run app/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.geo import clean_postcode, geocode_postcode  # noqa: E402
from pipeline.reference import MANUAL, PROCESSED, hospitals, procedures  # noqa: E402
from pipeline.score import overview  # noqa: E402

ACCESS_LABELS = {
    "gecontracteerd": "✅ Gecontracteerd",
    "gecontracteerd_met_plafond": "⚠️ Gecontracteerd, met omzetplafond",
    "vrije_keuze": "🔓 Vrije keuze (restitutie, tot marktconform tarief)",
    "in_onderhandeling": "⏳ In onderhandeling",
    "geen_contract": "❌ Geen contract",
    "onbekend": "❔ Onbekend",
}

st.set_page_config(page_title="Beterverzekerd", page_icon="🏥", layout="wide")
st.title("Beterverzekerd")
st.caption("Vergelijk zorgpolissen op de ziekenhuizen die ze voor jou inkopen, niet alleen op prijs.")

st.warning(
    "**Prototype.** Geen medisch of financieel advies. Contractstatus is geen garantie op toegang "
    "(omzetplafonds, vergoeding tijdens onderhandelingen). Controleer altijd bij je verzekeraar."
)


@st.cache_data(ttl=24 * 3600)
def cached_geocode(postcode: str):
    return geocode_postcode(postcode)


with st.form("zoek"):
    col1, col2, col3 = st.columns([2, 2, 1])
    postcode = col1.text_input("Postcode", value="3584 CX")
    procs = procedures()
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
        summary, detail = overview(coords[0], coords[1], procedure_id, radius_km=radius)
        # keep results across reruns (the polis selectbox below triggers one)
        st.session_state["result"] = {"summary": summary, "detail": detail, "radius": radius}

result = st.session_state.get("result")
if result:
    summary, detail = result["summary"], result["detail"]
    if detail.empty:
        st.info(f"Geen ziekenhuizen uit onze lijst binnen {result['radius']} km. "
                f"De lijst bevat nu {len(hospitals())} locaties.")
    else:
        contracts_file = MANUAL / "contracts.csv"
        if not contracts_file.exists() or pd.read_csv(contracts_file).empty:
            st.info("Er is nog geen gecontroleerde contractdata ingevoerd, daarom staat alles op 'Onbekend'. "
                    "Contractoverzichten van de ziekenhuizen worden opgehaald en eerst met de hand gecontroleerd.")
        st.subheader("Per polis")
        shown = summary.drop(columns=["naam"]).dropna(axis=1, how="all").rename(columns={
            "concern": "Concern", "label": "Label", "polis": "Polis", "polis_type": "Type",
            "premie_per_maand": "Premie p/m (€)", "ziekenhuizen_in_bereik": "Ziekenhuizen in bereik",
            "gecontracteerd": "Gecontracteerd", "met_omzetplafond": "Met plafond",
            "vrije_keuze": "Vrije keuze (restitutie)", "in_onderhandeling": "In onderhandeling",
            "geen_contract": "Geen contract", "onbekend": "Onbekend",
            "kortste_wachttijd_weken": "Kortste wachttijd (wk)",
        })
        st.dataframe(shown, hide_index=True, use_container_width=True)
        st.caption("Kortste wachttijd: alleen ziekenhuizen die gecontracteerd zijn of via restitutie vergoed worden.")

        st.subheader("Details per ziekenhuis")
        chosen = st.selectbox("Polis", summary["naam"].tolist())
        rows = detail[detail["naam"] == chosen].copy()
        rows["access"] = rows["access"].map(ACCESS_LABELS)
        st.dataframe(rows.drop(columns=["naam", "concern", "label", "polis"]).dropna(axis=1, how="all").rename(columns={
            "location": "Ziekenhuis", "distance_km": "Afstand (km)", "access": "Contract",
            "contract_peildatum": "Peildatum contract", "contract_source": "Bron contract",
            "wait_weeks": "Wachttijd (wk)", "wait_peildatum": "Peildatum wachttijd",
            "quality_indicators": "Openbare kwaliteitsindicatoren", "quality_year": "Verslagjaar",
        }), hide_index=True, use_container_width=True)

with st.expander("Over de data"):
    def status(path: Path, label: str) -> str:
        if not path.exists():
            return f"- **{label}**: nog geen data"
        df = pd.read_csv(path)
        return f"- **{label}**: {len(df)} rijen (`{path.relative_to(path.parents[2])}`)"
    st.markdown("\n".join([
        status(MANUAL / "contracts.csv", "Contracten (gecontroleerd)"),
        status(MANUAL / "polissen_2027.csv", "Polissen 2027"),
        status(PROCESSED / "waiting_times.csv", "Wachttijden (NZa)"),
        status(PROCESSED / "quality.csv", "Kwaliteitsindicatoren (Zorginzicht)"),
        f"- **Ziekenhuislocaties**: {len(hospitals())}",
        "",
        "Bronnen: Zorginstituut Nederland (Zorginzicht), NZa, contractoverzichten van ziekenhuizen en "
        "verzekeraars, PDOK. Wachttijden worden door ziekenhuizen zelf aangeleverd en niet gecontroleerd. "
        "We tonen bewust geen ranglijst: kleine aantallen en verschillen in patiëntengroepen maken die misleidend.",
    ]))
