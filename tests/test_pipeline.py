"""Tests on synthetic data. They check the logic, not the real file layouts (unknown until CI downloads them)."""

from __future__ import annotations

import json

import pandas as pd
import pytest

import pipeline.reference
from pipeline import contracts_parse, nza_ingest, zorginzicht_ingest
from pipeline.contract_status import combine, normalise_status, plafond_from_text, status_from_text
from pipeline.geo import clean_postcode, parse_point
from pipeline.reference import match_label, match_location, normalise
from pipeline.score import access_status, contract_for, haversine_km, hospitals_within, latest_waits, overview, to_date, truthy
from scrapers.common import find_links, safe_filename
from scrapers.nza_wachttijden import candidate_order, is_waiting_time_csv


TEST_RULES = pd.DataFrame([
    {"procedure_id": "heup", "indicator_code": None, "indicator_pattern": "revisie", "direction": "lower_better", "label_nl": "Revisie"},
    {"procedure_id": "heup", "indicator_code": None, "indicator_pattern": "complicat", "direction": "lower_better", "label_nl": "Diepe wondinfectie"},
    {"procedure_id": "heup", "indicator_code": None, "indicator_pattern": "prom|verbeter", "direction": "higher_better", "label_nl": "PROM"},
    {"procedure_id": "heup", "indicator_code": None, "indicator_pattern": "aantal", "direction": "volume", "label_nl": "Aantal"},
    {"procedure_id": "knie", "indicator_code": None, "indicator_pattern": "aantal", "direction": "volume", "label_nl": "Aantal"},
])


@pytest.fixture(autouse=True)
def pattern_rules(monkeypatch):
    """The product judges only indicators listed by code; tests use simple name patterns instead."""
    import pipeline.quality
    real = pd.read_csv(pipeline.quality.MANUAL / "indicators.csv")
    monkeypatch.setattr(pipeline.quality, "indicator_meta", lambda: pd.concat([real, TEST_RULES], ignore_index=True))


def test_real_rules_are_by_code_only():
    import pipeline.quality
    rules = pd.read_csv(pipeline.quality.MANUAL / "indicators.csv")
    assert rules["indicator_code"].notna().all() and rules["indicator_pattern"].isna().all()
    assert set(rules["direction"]) <= {"lower_better", "higher_better", "volume", "none"}


# --- reference matching -------------------------------------------------------------------

def test_normalise_strips_accents_and_stopwords():
    assert normalise("St. Antonius Ziekenhuis") == "antonius"
    assert normalise("Univé") == "unive"


@pytest.mark.parametrize("name,city,expected", [
    ("UMC Utrecht", None, "umcu"),
    ("Universitair Medisch Centrum Utrecht", None, "umcu"),
    ("Meander Medisch Centrum", None, "meander"),
    ("Jeroen Bosch Ziekenhuis", None, "jbz"),
    ("St. Antonius Ziekenhuis", "Nieuwegein", "antonius_nwg"),
    ("St. Antonius Ziekenhuis", "Utrecht", "antonius_utr"),
    ("St. Antonius Ziekenhuis", None, None),  # ambiguous without city
    ("Ziekenhuis Amstelland", None, None),
])
def test_match_location(name, city, expected):
    assert match_location(name, city=city) == expected


def test_match_label():
    assert match_label("Zilveren Kruis") == ("Achmea", "Zilveren Kruis")
    assert match_label("ZILVEREN KRUIS ") == ("Achmea", "Zilveren Kruis")
    assert match_label("Achmea") == ("Achmea", None)
    assert match_label("Univé") == ("VGZ", "Univé")
    assert match_label("Gecontracteerd") is None


# --- contract status -----------------------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("Gecontracteerd", ("gecontracteerd", None)),
    ("Gecontracteerd met omzetplafond", ("gecontracteerd", True)),
    ("Gecontracteerd, geen omzetplafond", ("gecontracteerd", False)),
    ("In onderhandeling", ("in_onderhandeling", None)),
    ("(Nog) geen contract: wel vergoed", ("in_onderhandeling", None)),
    ("Geen contract", ("geen_contract", None)),
    ("Niet gecontracteerd", ("geen_contract", None)),
    ("Ja", ("gecontracteerd", None)),
    ("Nee", ("geen_contract", None)),
    ("✓", ("gecontracteerd", None)),
    ("Niet-gecontracteerd", ("geen_contract", None)),
    ("niet\u00a0gecontracteerd", ("geen_contract", None)),
    ("Gecontracteerd. Omzetplafond: nee", ("gecontracteerd", False)),
    ("Gecontracteerd, geen contract voor budgetpolis", ("onbekend", None)),
    ("Contract opgezegd", ("geen_contract", None)),
    ("Contract volgt", ("in_onderhandeling", None)),
    ("x", ("gecontracteerd", None)),
    ("plafond n.v.t.", ("onbekend", False)),
    ("", ("onbekend", None)),
    (None, ("onbekend", None)),
    ("Omzetplafond", ("gecontracteerd", True)),
])
def test_normalise_status(text, expected):
    assert normalise_status(text) == expected


def test_parse_tables_row_and_column_layouts():
    row_layout = [["Verzekeraar", "Status 2027"],
                  ["Zilveren Kruis", "Gecontracteerd (omzetplafond)"],
                  ["CZ", "In onderhandeling"],
                  ["Toelichting", "zie website"]]
    column_layout = [["", "VGZ", "Menzis", "DSW"],
                     ["2027", "Ja", "Nee", "Gecontracteerd"]]
    rows = contracts_parse.parse_tables([row_layout, column_layout])
    got = {(r["label"] or r["concern"], r["status"], r["omzetplafond"]) for r in rows}
    assert ("Zilveren Kruis", "gecontracteerd", True) in got
    assert ("CZ", "in_onderhandeling", None) in got
    assert ("VGZ", "gecontracteerd", None) in got
    assert ("Menzis", "geen_contract", None) in got
    assert ("DSW", "gecontracteerd", None) in got


def test_peildatum_and_year():
    text = "Overzicht contracten zorgverzekeraars 2027\nPeildatum: 15 november 2026\nVoor 2027 geldt..."
    assert contracts_parse.find_peildatum(text) == "15 november 2026"
    assert contracts_parse.find_year(text) == 2027


def test_contracts_parse_main(tmp_path, monkeypatch):
    raw = tmp_path / "2026-11-24"
    raw.mkdir()
    (raw / "meta.json").write_text(json.dumps({"results": {"avl": {"url": "https://example.org/x.pdf", "location_ids": ["avl"]}}}))
    (raw / "avl.txt").write_text("Contracten 2027. Peildatum 01-11-2026")
    (raw / "avl.tables.json").write_text(json.dumps([[["CZ", "Gecontracteerd"]]]))
    monkeypatch.setattr(pipeline.reference, "PROCESSED", tmp_path / "out")
    assert contracts_parse.main([str(raw)]) == 0
    out = pd.read_csv(tmp_path / "out" / "contracts_candidates.csv")
    assert out.loc[0, "concern"] == "CZ" and out.loc[0, "year"] == 2027 and out.loc[0, "peildatum"] == "01-11-2026"


# --- scraper helpers -----------------------------------------------------------------------

def test_find_links():
    html = '<a href="/a.xlsx">x</a><a href="/other.pdf">pdf</a>'
    assert find_links(html, "https://x.nl/p/", r"\.xlsx") == ["https://x.nl/a.xlsx"]


def test_nza_candidate_order_and_csv_check():
    from scrapers.common import all_links
    html = ('<a href="/PUC/Handlers/DownloadDocument.ashx?identifier=PUC_659356_22&amp;versienummer=1">Toelichting (pdf)</a>'
            '<a href="/PUC/Handlers/DownloadDocument.ashx?identifier=PUC_809508_22&amp;versienummer=1">Bijlage</a>'
            '<a href="/PUC/Handlers/DownloadDocument.ashx?identifier=PUC_700000_22&amp;versienummer=1">Dataset wachttijden (csv)</a>'
            '<a href="/over">Over</a>')
    order = candidate_order(all_links(html, "https://puc.overheid.nl/nza/doc/PUC_651798_22/"))
    assert len(order) == 3 and "PUC_700000" in order[0] and "PUC_809508" in order[1]
    assert is_waiting_time_csv(b"PEILDATUM;AGB;NAAM;SPECIALISME;WACHTTIJD\n2026-09-15;1;x;y;3\n")
    assert not is_waiting_time_csv(b"%PDF-1.7 ...")


def test_safe_filename():
    assert safe_filename("https://x.nl/a/Open%20data.xlsx") == "Open_20data.xlsx"
    assert safe_filename("https://x.nl/dl", 'attachment; filename="MSZ 2025.xlsx"') == "MSZ_2025.xlsx"


# --- ingest on synthetic files -------------------------------------------------------------

def test_zorginzicht_ingest(tmp_path, monkeypatch):
    raw = tmp_path / "2026-11-24"
    raw.mkdir()
    base = {"Sector": "Medisch-specialistische zorg", "KvkNummer": "41179410", "LocatieAGBCode": None,
            "Vestigingsnummer": "1", "LocatieHuisnummer": "100", "Type Zorgaanbieder": "Ziekenhuis",
            "IndicatorEenheid": "Percentage", "IndicatorType": "Uitkomst", "Thema": "t", "IndicatorNummer": "1",
            "Indicator_nvt": "0", "Aantal waarnemingen (N)": None}
    def row(**kw):
        return {**base, **kw}
    odb = pd.DataFrame([
        row(Verslagjaar="2025", OrganisatieNaam="UMC Utrecht", OrganisatieAGBCode="6020602", LocatieNaam="UMC Utrecht",
            LocatiePostcode="3584 CX", LocatiePlaats="Utrecht", IndicatorsetCode="ISID1", IndicatorsetNaam="Heupprothese",
            IndicatorCode="IN1", IndicatorNaam="Revisie", IndicatorWaarde="1.0", Teller="2", Noemer="200"),
        row(Verslagjaar="2025", OrganisatieNaam="UMC Utrecht", OrganisatieAGBCode="6020602", LocatieNaam="UMC Utrecht",
            LocatiePostcode="3584CX", LocatiePlaats="Utrecht", IndicatorsetCode="ISID2", IndicatorsetNaam="Heupfractuur",
            IndicatorCode="IN9", IndicatorNaam="Iets anders", IndicatorWaarde="5", Teller=None, Noemer=None),
        row(Verslagjaar="2025", OrganisatieNaam="Oogkliniek", OrganisatieAGBCode="22220000", LocatieNaam="Oogkliniek",
            LocatiePostcode="1000AA", LocatiePlaats="Amsterdam", IndicatorsetCode="ISID3", IndicatorsetNaam="Cataract",
            IndicatorCode="IN5", IndicatorNaam="Visuswinst", IndicatorWaarde="95", Teller="95", Noemer="100"),
    ])
    with pd.ExcelWriter(raw / "openbaar-databestand-msz-verslagjaar-2025.xlsx") as writer:
        pd.DataFrame({"Datum wijzging": ["x"], "wijziging": ["y"]}).to_excel(writer, sheet_name="Versiebeheer", index=False)
        odb.to_excel(writer, sheet_name="ODB MSZ vj2025", index=False)
    late = odb.iloc[[0]].assign(Teller="1", Noemer="200")
    late.to_excel(raw / "naleveringen-msz-verslagjaar-2025.xlsx", index=False)
    monkeypatch.setattr(zorginzicht_ingest, "REFERENCE", tmp_path / "ref")
    monkeypatch.setattr(zorginzicht_ingest, "CATALOGUE_DOC", tmp_path / "ind.md")
    monkeypatch.setattr(zorginzicht_ingest, "SET_INVENTORY", tmp_path / "sets.md")
    monkeypatch.setattr(pipeline.reference, "PROCESSED", tmp_path / "out")
    assert zorginzicht_ingest.main([str(raw)]) == 0

    locations = pd.read_csv(tmp_path / "ref" / "locations_zorginzicht.csv", dtype=str)
    assert set(locations["location_key"]) == {"06020602-3584CX", "22220000-1000AA"}  # all sets, AGB zero-padded
    catalogue = pd.read_csv(tmp_path / "ref" / "indicators.csv", dtype=str)
    assert set(catalogue["indicator_code"]) == {"IN1", "IN5"}  # Heupfractuur excluded
    m = pd.read_csv(tmp_path / "out" / "measurements.csv", dtype=str)
    assert sorted(m["procedure_id"]) == ["heup", "staar"]
    assert m.set_index("indicator_code").loc["IN1", "numerator"] == "1"  # nalevering wins
    assert "Revisie" in (tmp_path / "ind.md").read_text()


def test_nza_ingest(tmp_path, monkeypatch):
    header = "PEILDATUM;AGBCODE;POSTCODE;NAAM_VESTIGING;PLAATS;TYPE_WACHTTIJD;OMS_WACHTTIJD;WACHTTIJD;INSUFFICIENT_OBSERVATIONS"
    rows = ["2026-11-10;06020602;3584CX;UMC Utrecht;Utrecht;Behandeling;Initiële totale heupvervanging (orthopedie);49;FALSE",
            "2026-11-10;06020602;3584CX;UMC Utrecht;Utrecht;Polikliniekbezoek;Orthopedie - Heupklachten;14;FALSE",
            "2026-11-10;06020602;3584CX;UMC Utrecht;Utrecht;Behandeling;Initiële staaroperatie (oogheelkunde);30;TRUE",
            "2026-11-10;06020602;3584CX;UMC Utrecht;Utrecht;Polikliniekbezoek;Cardiologie - Algemeen;3;FALSE"]
    path = tmp_path / "wachttijden_2026-11-10.csv"
    path.write_bytes(("\n".join([header] + rows) + "\n").encode("cp1252"))
    monkeypatch.setattr(pipeline.reference, "PROCESSED", tmp_path / "out")
    monkeypatch.setattr(nza_ingest, "INVENTORY", tmp_path / "inventory.md")
    assert nza_ingest.main([str(path)]) == 0
    out = pd.read_csv(tmp_path / "out" / "waiting_times.csv", dtype=str)
    assert sorted(out["procedure_id"]) == ["heup", "heup", "staar"]   # cardiology dropped
    heup = out[(out["procedure_id"] == "heup") & (out["wait_type"] == "behandeling")].iloc[0]
    assert float(heup["days"]) == 49 and float(heup["weeks"]) == 7 and heup["location_key"].startswith("06020602-")
    from pipeline.score import latest_waits
    waits = latest_waits("staar", pd.read_csv(tmp_path / "out" / "waiting_times.csv"))
    assert waits.empty  # too few observations: not shown

# --- scoring -------------------------------------------------------------------------------

def test_haversine_and_radius():
    assert haversine_km(52.0907, 5.1214, 52.3676, 4.9041) == pytest.approx(34, abs=2)  # Utrecht–Amsterdam
    near = hospitals_within(52.0870, 5.1790, 10)
    assert near.iloc[0]["location_id"] == "umcu"
    assert "jbz" not in set(near["location_id"])


def test_contract_for_prefers_label_then_concern_and_latest():
    contracts = pd.DataFrame([
        {"organisatie_agb": "06020602", "concern": "CZ", "label": None, "status": "geen_contract", "peildatum": "2026-11-01"},
        {"organisatie_agb": "06020602", "concern": "CZ", "label": None, "status": "gecontracteerd", "peildatum": "2026-12-01"},
        {"organisatie_agb": "06020602", "concern": "CZ", "label": "OHRA", "status": "in_onderhandeling", "peildatum": "2026-11-15"},
    ])
    assert contract_for(contracts, "06020602", "CZ", "CZ")["status"] == "gecontracteerd"
    assert contract_for(contracts, "06020602", "CZ", "OHRA")["status"] == "in_onderhandeling"
    assert contract_for(contracts, "06020602", "VGZ", "VGZ") is None


def test_access_status():
    assert access_status({"polis_type": "Restitutie"}, None) == "vrije_keuze"
    assert access_status({"polis_type": "Restitutiepolis "}, None) == "vrije_keuze"
    assert access_status({}, {"status": "gecontracteerd", "omzetplafond": 1.0}) == "gecontracteerd_met_plafond"
    assert access_status({"polis_type": "natura"}, None) == "onbekend"
    assert access_status({}, {"status": "gecontracteerd", "omzetplafond": True}) == "gecontracteerd_met_plafond"
    assert access_status({}, {"status": "geen_contract"}) == "geen_contract"


def test_overview_end_to_end():
    policies = pd.DataFrame([
        {"concern": "CZ", "label": "CZ", "polis": "CZ Zorgbewust", "polis_type": "natura", "premie_per_maand": 150},
        {"concern": "VGZ", "label": "VGZ", "polis": "VGZ Ruime Keuze", "polis_type": "restitutie", "premie_per_maand": 170},
    ])
    contracts = pd.DataFrame([
        {"location_id": "umcu", "concern": "CZ", "label": None, "status": "gecontracteerd", "omzetplafond": True, "peildatum": "2026-11-15"},
        {"location_id": "diak_utr", "concern": "CZ", "label": None, "status": "gecontracteerd", "omzetplafond": False, "peildatum": "2026-11-15"},
    ])
    waits = pd.DataFrame([
        {"procedure_id": "heup", "location_key": "06020602-3584CX", "weeks": 9, "wait_type": "Behandeling", "peildatum": "2026-09-15"},
        {"procedure_id": "heup", "location_key": "06010618-3582KE", "weeks": 5, "wait_type": "Behandeling", "peildatum": "2026-09-15"},
        {"procedure_id": "heup", "location_key": "06010618-3582KE", "weeks": 2, "wait_type": "Polikliniek", "peildatum": "2026-09-15"},
    ])
    quality = pd.DataFrame([
        # umcu: 1/1000 revisions vs national ~5% -> clearly better
        {"procedure_id": "heup", "location_key": "06020602-3584CX", "indicator": "Revisie binnen 1 jaar", "numerator": 1, "denominator": 1000, "verslagjaar": "2025"},
        {"procedure_id": "heup", "location_key": None, "indicator": "Revisie binnen 1 jaar", "numerator": 500, "denominator": 9000, "verslagjaar": "2025"},
    ])
    from pipeline.score import manual_locations
    summary, detail = overview(52.0870, 5.1790, "heup", radius_km=6, policies=policies,
                               contracts=contracts, waits=waits, quality=quality, hospital_table=manual_locations())
    cz = summary.set_index("polis").loc["CZ Zorgbewust"]
    # the Diakonessenhuis contract is per organisation, so it covers Utrecht and Zeist
    assert cz["gecontracteerd"] == 2 and cz["met_omzetplafond"] == 1
    assert cz["kortste_wachttijd_weken"] == 5  # treatment wait, not outpatient
    vgz = summary.set_index("polis").loc["VGZ Ruime Keuze"]
    assert vgz["onbekend"] == 0 and vgz["vrije_keuze"] == vgz["ziekenhuizen_in_bereik"]
    assert vgz["gecontracteerd"] == 0  # restitutie is not a contract
    umcu = detail[(detail["polis"] == "CZ Zorgbewust") & (detail["location"] == "UMC Utrecht Heidelberglaan")].iloc[0]
    assert umcu["quality"] == "boven_gemiddeld" and umcu["quality_better"] == 1
    assert cz["kwaliteit_boven_gemiddeld"] == 1


def test_overview_without_policy_file_falls_back_to_labels():
    from pipeline.score import manual_locations
    summary, _ = overview(52.0870, 5.1790, "heup", radius_km=6, contracts=pd.DataFrame(),
                          waits=pd.DataFrame(), quality=pd.DataFrame(), hospital_table=manual_locations())
    assert len(summary) >= 4 and summary["onbekend"].gt(0).all()  # the four insurers in scope


# --- geo -----------------------------------------------------------------------------------

def test_postcode_helpers():
    assert clean_postcode("3584 cx") == "3584CX"
    assert clean_postcode("3584") == "3584"
    assert clean_postcode("ABCD") is None
    assert parse_point("POINT(5.179 52.087)") == (52.087, 5.179)


# --- regressions from code review ----------------------------------------------------------

def test_row_layout_with_plafond_column():
    table = [["Verzekeraar", "Gecontracteerd", "Omzetplafond"],
             ["Zilveren Kruis", "Ja", "Nee"],
             ["CZ", "Ja", "Ja"],
             ["VGZ", "Nee", ""]]
    got = {r["label"] or r["concern"]: (r["status"], r["omzetplafond"]) for r in contracts_parse.parse_tables([table])}
    assert got["Zilveren Kruis"] == ("gecontracteerd", False)
    assert got["CZ"] == ("gecontracteerd", True)
    assert got["VGZ"][0] == "geen_contract"


def test_conflicting_cells_are_flagged_unknown():
    assert combine(["gecontracteerd", "geen_contract"]) == "onbekend"
    rows = contracts_parse.parse_tables([[["CZ", "Gecontracteerd", "Geen contract"]]])
    assert rows and rows[0]["status"] == "onbekend"


def test_label_aliases():
    assert match_label("Ditzo") == ("a.s.r.", "Ik kies zelf")
    assert match_label("Anderzorg") == ("Menzis", "Menzis")
    assert match_label("Pro Life") == ("Achmea", "De christelijke zorgverzekeraar")


def test_line_fallback_for_html_pages():
    text = "Stand van zaken 13 november 2026\nZilveren Kruis: gecontracteerd\nCZ - in onderhandeling\nWelkom bij ons ziekenhuis"
    rows = contracts_parse.parse_tables(contracts_parse.line_tables(text))
    got = {r["label"] or r["concern"]: (r["label"], r["status"]) for r in rows}
    # 'CZ' alone (no other CZ labels named) speaks for the whole concern: label None
    assert got == {"Zilveren Kruis": ("Zilveren Kruis", "gecontracteerd"), "CZ": (None, "in_onderhandeling")}


def test_year_most_frequent_not_highest():
    assert contracts_parse.find_year("Contracten 2027 ... 2027 ... meerjarenafspraak 2026-2029") == 2027


def test_missing_name_does_not_match_any_hospital():
    assert match_location(float("nan")) is None
    assert match_location("nan") is None


def test_one_pdf_rows_for_every_location(tmp_path, monkeypatch):
    raw = tmp_path / "2026-11-24"
    raw.mkdir()
    (raw / "meta.json").write_text(json.dumps({"results": {"antonius_nwg": {
        "url": "https://example.org/a.pdf", "format": "pdf", "location_ids": ["antonius_nwg", "antonius_utr"]}}}))
    (raw / "antonius_nwg.txt").write_text("2027")
    (raw / "antonius_nwg.tables.json").write_text(json.dumps([[["CZ", "Gecontracteerd"]]]))
    monkeypatch.setattr(pipeline.reference, "PROCESSED", tmp_path / "out")
    assert contracts_parse.main([str(raw)]) == 0
    out = pd.read_csv(tmp_path / "out" / "contracts_candidates.csv")
    assert set(out["location_id"]) == {"antonius_nwg", "antonius_utr"}
    assert (tmp_path / "out" / "history" / "contracts_candidates" / "2026-11-24.csv").exists()


def test_dates_and_truthy():
    assert to_date("15 oktober 2026") < to_date("1 december 2026")
    assert to_date("01-11-2026") == pd.Timestamp(2026, 11, 1)
    assert to_date("2026-11-01") == pd.Timestamp(2026, 11, 1)
    assert pd.isna(to_date(None))
    assert truthy(1.0) and truthy("ja") and not truthy(float("nan")) and not truthy("")


def test_contract_latest_by_real_date():
    contracts = pd.DataFrame([
        {"organisatie_agb": "06020602", "concern": "CZ", "label": None, "status": "in_onderhandeling", "peildatum": "15 oktober 2026"},
        {"organisatie_agb": "06020602", "concern": "CZ", "label": None, "status": "gecontracteerd", "peildatum": "1 december 2026"},
    ])
    assert contract_for(contracts, "06020602", "CZ", "CZ")["status"] == "gecontracteerd"


def test_treatment_wait_preference_is_per_location():
    waits = pd.DataFrame([
        {"procedure_id": "heup", "location_key": "umcu", "weeks": 9, "wait_type": "Behandeling", "peildatum": "2026-09-15"},
        {"procedure_id": "heup", "location_key": "umcu", "weeks": 3, "wait_type": "Polikliniek", "peildatum": "2026-09-15"},
        {"procedure_id": "heup", "location_key": "meander", "weeks": 4, "wait_type": "Polikliniek", "peildatum": "2026-09-15"},
    ])
    got = latest_waits("heup", waits).set_index("location_key")["weeks"].to_dict()
    assert got == {"umcu": 9, "meander": 4}


def test_duplicate_polis_names_across_labels_stay_separate():
    policies = pd.DataFrame([
        {"concern": "VGZ", "label": "VGZ", "polis": "Basis", "polis_type": "natura", "premie_per_maand": 150},
        {"concern": "CZ", "label": "CZ", "polis": "Basis", "polis_type": "natura", "premie_per_maand": 160},
    ])
    from pipeline.score import manual_locations
    summary, detail = overview(52.0870, 5.1790, "heup", radius_km=6, policies=policies,
                               contracts=pd.DataFrame(), waits=pd.DataFrame(), quality=pd.DataFrame(),
                               hospital_table=manual_locations())
    assert len(summary) == 2
    assert summary.set_index("naam")["premie_per_maand"].to_dict() == {"VGZ – Basis": 150, "CZ – Basis": 160}



def test_non_data_sheets_are_ignored():
    assert zorginzicht_ingest.canonical(pd.DataFrame(columns=["Datum wijzging", "IndicatorsetCode", "IndicatorsetNaam"])) is None
    assert zorginzicht_ingest.agb("6010901") == "06010901" and zorginzicht_ingest.agb(6010901.0) == "06010901"
    assert zorginzicht_ingest.postcode("3584 cx") == "3584CX" and zorginzicht_ingest.postcode("x") is None



def test_read_any_robustness(tmp_path):
    from pipeline.tabular import read_any
    (tmp_path / "empty.csv").write_bytes(b"")
    (tmp_path / "odd.csv").write_bytes(b"a;b\n\x81x;\x8dy\n")
    assert read_any(tmp_path / "empty.csv") == {}
    assert list(read_any(tmp_path / "odd.csv")["csv"].columns) == ["a", "b"]
    (tmp_path / "bad.zip").write_bytes(b"not a zip")
    assert read_any(tmp_path / "bad.zip") == {}


def test_extract_html_tables_and_text():
    from scrapers.contracts import extract_html
    page = ("<html><head><script>var x=1;</script></head><body><h1>Contracten 2027</h1>"
            "<p>Peildatum: 13 november 2026</p><ul><li>Zilveren Kruis: gecontracteerd</li></ul>"
            "<table><tr><th>Verzekeraar</th><th>Status</th></tr><tr><td>CZ</td><td>In onderhandeling</td></tr></table>"
            "</body></html>")
    text, tables = extract_html(page)
    assert "var x" not in text and "Zilveren Kruis: gecontracteerd" in text
    assert contracts_parse.find_peildatum(text) == "13 november 2026"
    rows = contracts_parse.parse_tables(tables)
    assert [(r["concern"], r["status"]) for r in rows] == [("CZ", "in_onderhandeling")]



# --- regressions from second review --------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("Geen contract afgesloten", "geen_contract"),
    ("Ja*", "gecontracteerd"), ("Nee*", "geen_contract"), ("Ja¹", "gecontracteerd"), ("Ja (1)", "gecontracteerd"),
    ("Ja, zonder omzetplafond", "gecontracteerd"),
    ("Wel contract", "gecontracteerd"), ("Contract getekend", "gecontracteerd"), ("Akkoord", "gecontracteerd"),
    ("Nog in gesprek", "in_onderhandeling"), ("nog niet gecontracteerd", "in_onderhandeling"),
    ("gecontracteerd (m.u.v. budgetpolis)", "onbekend"), ("Gecontracteerd, behalve budgetpolis", "onbekend"),
    ("Wij zijn niet gecontracteerd voor de Bewuzt polis, wel voor de overige polissen", "onbekend"),
])
def test_status_phrases(text, expected):
    assert status_from_text(text) == expected


def test_html_table_with_empty_cell_and_no_th():
    from scrapers.contracts import extract_html
    page = ("<table><tr><td>Zorgverzekeraar</td><td>Contract 2027</td><td>Omzetplafond</td></tr>"
            "<tr><td>Zilveren Kruis</td><td>Ja</td><td>Nee</td></tr>"
            "<tr><td>VGZ</td><td>Ja</td><td>Ja</td></tr>"
            "<tr><td>CZ</td><td></td><td></td></tr></table>")
    _, tables = extract_html(page)
    json.dumps(tables, allow_nan=False)  # valid JSON: no NaN
    got = {r["label"] or r["concern"]: (r["status"], r["omzetplafond"]) for r in contracts_parse.parse_tables(tables)}
    assert got["Zilveren Kruis"] == ("gecontracteerd", False)
    assert got["VGZ"] == ("gecontracteerd", True)
    assert "CZ" not in got


def test_column_layout_with_plafond_row():
    table = [["", "Zilveren Kruis", "VGZ"], ["Contract 2027", "Ja", "Ja"], ["Omzetplafond", "Nee", "Ja"]]
    rows = contracts_parse.parse_tables([table])
    got = {r["label"] or r["concern"]: (r["status"], r["omzetplafond"]) for r in rows}
    assert len(rows) == 2
    assert got == {"Zilveren Kruis": ("gecontracteerd", False), "VGZ": ("gecontracteerd", True)}


def test_concern_and_label_columns():
    table = [["Concern", "Label", "Status"],
             ["VGZ", "IZA", "Gecontracteerd"],
             ["CZ", "OHRA", "Nee"],
             ["Achmea", "Zilveren Kruis", "Ja"]]
    got = {(r["concern"], r["label"]): r["status"] for r in contracts_parse.parse_tables([table])}
    assert got == {("VGZ", "IZA"): "gecontracteerd", ("CZ", "OHRA"): "geen_contract",
                   ("Achmea", "Zilveren Kruis"): "gecontracteerd"}


def test_concern_name_is_label_when_table_lists_other_labels():
    table = [["Verzekeraar", "Status"], ["VGZ", "Ja"], ["IZA", "Nee"], ["CZ", "Ja"]]
    got = {(r["concern"], r["label"]): r["status"] for r in contracts_parse.parse_tables([table])}
    assert got == {("VGZ", "VGZ"): "gecontracteerd", ("VGZ", "IZA"): "geen_contract", ("CZ", None): "gecontracteerd"}


def test_lines_are_independent_tables():
    text = "Zilveren Kruis | VGZ\nWij hebben een contract: ja\nCZ: geen contract"
    got = {r["label"] or r["concern"]: r["status"] for r in contracts_parse.parse_tables(contracts_parse.line_tables(text))}
    assert got == {"CZ": "geen_contract"}


def test_shared_status_for_several_concerns_and_policy_rows():
    rows = contracts_parse.parse_tables([[["Menzis", "DSW", "gecontracteerd"]]])
    assert {r["concern"] for r in rows} == {"Menzis", "DSW"}
    rows = contracts_parse.parse_tables([[["Verzekeraar", "Polis", "Status"], ["VGZ", "VGZ Bewuzt", "Geen contract"], ["IZA", "", "Ja"]]])
    bewuzt = next(r for r in rows if r["label"] == "VGZ")
    assert bewuzt["polis"] == "VGZ Bewuzt" and bewuzt["status"] == "geen_contract"


def test_year_and_peildatum_edge_cases():
    text = "Overzicht contracten zorgverzekeraars 2027\nPeildatum 1-11-2026\nVorig jaar 2026 en 2026"
    assert contracts_parse.find_year(text) == 2027
    assert contracts_parse.find_peildatum("Versie 2.1, 1 november 2026") == "1 november 2026"
    assert contracts_parse.find_peildatum("Bijgewerkt op 1 okt. 2026") == "1 okt. 2026"


def test_to_date_variants():
    assert to_date("2026/11/01") == pd.Timestamp(2026, 11, 1)
    assert to_date("1 okt. 2026") == pd.Timestamp(2026, 10, 1)
    assert to_date("15-okt-2026") == pd.Timestamp(2026, 10, 15)
    assert to_date(pd.Timestamp(2026, 1, 2)) == pd.Timestamp(2026, 1, 2)


def test_latest_waits_newer_outpatient_beats_old_treatment():
    waits = pd.DataFrame([
        {"procedure_id": "heup", "location_key": "umcu", "weeks": 9, "wait_type": "Behandeling", "peildatum": "2026-01-15"},
        {"procedure_id": "heup", "location_key": "umcu", "weeks": 3, "wait_type": "Polikliniek", "peildatum": "2026-09-15"},
        {"procedure_id": "heup", "location_key": "umcu", "weeks": None, "wait_type": "Behandeling", "peildatum": "2026-09-15"},
    ])
    assert latest_waits("heup", waits).set_index("location_key")["weeks"].to_dict() == {"umcu": 3}


def test_parse_main_survives_bad_file(tmp_path, monkeypatch):
    raw = tmp_path / "2026-11-24"
    raw.mkdir()
    (raw / "meta.json").write_text(json.dumps({"results": {}}))
    (raw / "bad.tables.json").write_text("{not json")
    (raw / "bad.txt").write_text("")
    (raw / "good.tables.json").write_text(json.dumps([[["CZ", "Ja"]]]))
    (raw / "good.txt").write_text("contracten 2027")
    monkeypatch.setattr(pipeline.reference, "PROCESSED", tmp_path / "out")
    assert contracts_parse.main([str(raw)]) == 0
    assert len(pd.read_csv(tmp_path / "out" / "contracts_candidates.csv")) == 1



# --- quality comparison (the USP) ----------------------------------------------------------

from pipeline.quality import compare, direction_for, hospital_verdict, wilson  # noqa: E402


def test_wilson_interval():
    low, high = wilson(0, 20)
    assert low == 0 and 0.15 < high < 0.17
    low, high = wilson(50, 1000)
    assert 0.037 < low < 0.05 < high < 0.066


def test_direction_lookup():
    assert direction_for("heup", "Revisie binnen 1 jaar na primaire THP")[0] == "lower_better"
    assert direction_for("knie", "Aantal primaire TKP")[0] == "volume"
    assert direction_for("heup", "Onbekende indicator") == (None, None)


def _quality_rows(rows):
    return pd.DataFrame([{"procedure_id": "heup", "indicator": ind, "location_key": loc, "numerator": n,
                          "denominator": d, "verslagjaar": "2025", "value": None} for loc, ind, n, d in rows])


def test_small_hospital_is_not_called_worse():
    # national ~5%; small hospital 2/20 = 10% but interval includes 5% -> 'gemiddeld'
    df = compare(_quality_rows([("small", "Revisie", 2, 20), (None, "Revisie", 500, 10000)]))
    assert df.set_index("location_key").loc["small", "verdict"] == "gemiddeld"


def test_large_hospital_difference_is_shown():
    df = compare(_quality_rows([("bad", "Revisie", 150, 1000), ("good", "Revisie", 10, 1000), (None, "Revisie", 500, 10000)]))
    verdicts = df.dropna(subset=["location_key"]).set_index("location_key")["verdict"].to_dict()
    assert verdicts == {"bad": "slechter", "good": "beter"}


def test_higher_better_and_unknown_direction():
    df = compare(_quality_rows([("a", "PROM verbetering", 950, 1000), (None, "PROM verbetering", 7000, 10000),
                                ("a", "Iets onbekends", 5, 10)]))
    by = df[df["location_key"] == "a"].set_index("indicator")["verdict"]
    assert by["PROM verbetering"] == "beter" and pd.isna(by["Iets onbekends"])


def test_hospital_verdict_summary():
    df = compare(_quality_rows([("x", "Revisie", 10, 1000), ("x", "Complicaties", 200, 1000),
                                (None, "Revisie", 500, 10000), (None, "Complicaties", 500, 10000),
                                ("y", "Revisie", 1, 10)]))
    v = hospital_verdict(df, "heup").set_index("location_key")["quality_verdict"].to_dict()
    assert v == {"x": "gemengd", "y": "gemiddeld"}


def test_contract_page_follows_overview_links_and_decodes_utf8():
    from types import SimpleNamespace
    from scrapers.contracts import decode_html, linked_documents
    page = ('<a href="/media/abc/status-afspraken-2027.pdf">Bekijk de status afspraken zorgverzekeraars 2027</a>'
            '<a href="/media/logo.png">logo</a><a href="https://elders.nl/x.pdf">overzicht</a>'
            '<a href="/contact">Contact</a>')
    docs = linked_documents(page, "https://www.antoniusziekenhuis.nl/kosten-en-zorgverzekering/contracten")
    assert docs == ["https://www.antoniusziekenhuis.nl/media/abc/status-afspraken-2027.pdf"]
    resp = SimpleNamespace(content="Patiënt".encode("utf-8"), apparent_encoding="utf-8")
    assert decode_html(resp) == "Patiënt"


def test_geocode_house_number():
    from pipeline.geocode import house_number
    assert house_number("114") == "114" and house_number("1 a") == "1" and house_number(None) == "" and house_number(float("nan")) == ""


# --- DuckDB ---------------------------------------------------------------------------------

def test_build_db_quality_over_years(tmp_path, monkeypatch):
    import duckdb
    from pipeline import build_db
    ref, proc = tmp_path / "ref", tmp_path / "proc"
    ref.mkdir(), proc.mkdir()
    pd.DataFrame([
        {"location_key": "06020602-3584CX", "organisatie_agb": "06020602", "organisatie_naam": "UMC Utrecht",
         "locatie_naam": "UMC Utrecht", "postcode": "3584CX", "plaats": "Utrecht", "lat": 52.087, "lon": 5.179},
        {"location_key": "11111111-1000AA", "organisatie_agb": "11111111", "organisatie_naam": "Ander",
         "locatie_naam": "Ander", "postcode": "1000AA", "plaats": "Amsterdam", "lat": 52.37, "lon": 4.9},
        {"location_key": "22220841-3735ME", "organisatie_agb": "22220841", "organisatie_naam": "Gestopt",
         "locatie_naam": "Gestopt", "postcode": "3735ME", "plaats": "Bosch en Duin", "lat": 52.12, "lon": 5.24},
    ]).to_csv(ref / "locations.csv", index=False)
    pd.DataFrame([{"indicator_code": "IN1", "procedure_id": "heup", "thema": "Revisie", "indicator_naam": "Revisie binnen 1 jaar",
                   "eenheid": "Percentage", "indicator_type": "Uitkomst"}]).to_csv(ref / "indicators.csv", index=False)
    rows = []
    for year, (umc, other) in {2024: ((40, 1000), (40, 1000)), 2025: ((5, 1000), (60, 1000))}.items():
        rows += [{"procedure_id": "heup", "verslagjaar": year, "location_key": "06020602-3584CX", "indicator_code": "IN1",
                  "value": None, "numerator": umc[0], "denominator": umc[1], "source": "t"},
                 {"procedure_id": "heup", "verslagjaar": year, "location_key": "11111111-1000AA", "indicator_code": "IN1",
                  "value": None, "numerator": other[0], "denominator": other[1], "source": "t"},
                 {"procedure_id": "heup", "verslagjaar": year, "location_key": "99999999-9999ZZ", "indicator_code": "IN1",
                  "value": None, "numerator": 1, "denominator": 10, "source": "t"}]
    rows.append({"procedure_id": "heup", "verslagjaar": 2023, "location_key": "22220841-3735ME", "indicator_code": "IN1",
                 "value": None, "numerator": 1, "denominator": 1000, "source": "t"})  # stopped reporting after 2023
    pd.DataFrame(rows).to_csv(proc / "measurements.csv", index=False)
    monkeypatch.setattr(build_db, "REFERENCE", ref)
    monkeypatch.setattr(build_db, "PROCESSED", proc)
    path = build_db.build(tmp_path / "t.duckdb")
    con = duckdb.connect(str(path), read_only=True)
    trend = con.execute("SELECT verslagjaar, quality_verdict FROM v_quality_trend "
                        "WHERE location_key = '06020602-3584CX' ORDER BY verslagjaar").fetchall()
    assert trend == [(2024, "gemiddeld"), (2025, "boven_gemiddeld")]  # improvement becomes visible
    latest = dict(con.execute("SELECT location_key, quality_verdict FROM v_quality_latest").fetchall())
    assert latest["11111111-1000AA"] == "onder_gemiddeld"
    assert "22220841-3735ME" not in latest  # an old verdict of a location that stopped is not current
    from pipeline.db_queries import locations_for_procedure
    assert "22220841-3735ME" not in set(locations_for_procedure(con, "heup")["location_key"])
    problems = dict(con.execute("SELECT problem, n FROM v_integrity").fetchall())
    assert problems["measurement without location"] == 2  # unknown location is reported, not silently dropped
    assert problems["duplicate location_key"] == 0
    from pipeline.quality_monitor import build_report
    report = build_report(con)
    assert "## Heupprothese" in report and "Verbeterd van 2024 naar 2025" in report
    assert "UMC Utrecht (Utrecht)" in report.split("Verbeterd van 2024 naar 2025")[1]


def test_prom_means_are_shown_not_judged():
    df = compare(pd.DataFrame([
        {"procedure_id": "heup", "indicator": "Verschilscore PROMs heup, 12 maanden", "location_key": "a",
         "numerator": None, "denominator": None, "value": "30", "n_waarnemingen": 100, "verslagjaar": "2025"},
        {"procedure_id": "heup", "indicator": "Verschilscore PROMs heup, 12 maanden", "location_key": "b",
         "numerator": None, "denominator": None, "value": "20", "n_waarnemingen": 300, "verslagjaar": "2025"},
    ]))
    a = df.set_index("location_key").loc["a"]
    assert a["method"] == "mean" and pd.isna(a["verdict"])
    assert a["national_rate"] == pytest.approx(22.5)  # weighted by patients
    assert a["position"] == "gunstiger"  # PROM 'verbetering' rule: higher_better



def test_published_intervals_are_judged_with_official_ci():
    base = "Verschilscore tussen heup PROM preoperatief en 12 maanden na ingreep. EQ-5D index score. "
    rev = "Gecorrigeerd percentage revisie binnen 1 jaar na primaire THP. "
    rows = []
    for loc, (pt, lo, hi), (r, rlo, rhi), resp in [("a", (0.45, 0.42, 0.48), (0.2, 0.0, 0.5), 90),
                                                     ("b", (0.33, 0.30, 0.36), (1.0, 0.5, 1.5), 90),
                                                     ("c", (0.20, 0.15, 0.25), (3.0, 2.2, 3.9), 30),
                                                     ("d", (0.34, 0.20, 0.50), (9.0, 1.0, 2.0), 90)]:
        for suffix, v in [("Gemiddelde", pt), ("95% Betrouwbaarheidsinterval Lower bound", lo),
                          ("95% Betrouwbaarheidsinterval Upper bound", hi), ("Aantal (N)", 100)]:
            rows.append({"indicator": base + suffix, "value": str(v)})
        for suffix, v in [("Gecorrigeerd percentage", r), ("95% Betrouwbaarheidsinterval Lower bound", rlo),
                          ("95% Betrouwbaarheidsinterval Upper bound", rhi)]:
            rows.append({"indicator": rev + suffix, "value": str(v)})
        rows.append({"indicator": "Responspercentage pre-operatief heup PROMs", "value": str(resp)})
        for r_ in rows[-8:]:
            r_.update(procedure_id="heup", location_key=loc, verslagjaar="2025", numerator=None, denominator=None)
    out = compare(pd.DataFrame(rows))
    judged = out[out["method"] == "interval"]
    prom = judged[judged["indicator_nl"].str.startswith("Verbetering")].set_index("location_key")
    revision = judged[judged["indicator_nl"].str.contains("revisie")].set_index("location_key")
    assert prom.loc["a", "verdict"] == "beter"            # whole interval above the national median
    assert pd.isna(prom.loc["c", "verdict"]) and "respons" in prom.loc["c", "position"]  # low PROM response
    assert revision.loc["a", "verdict"] == "beter"        # lower revision is better
    assert revision.loc["c", "verdict"] == "slechter"
    assert pd.isna(revision.loc["d", "verdict"]) and revision.loc["d", "position"] == "inconsistent in bron"
    assert revision.loc["a", "indicator_nl"] == "Heroperatie (revisie) binnen 1 jaar"
    # interval rows are not also treated as plain means
    assert not ((out["method"] == "mean") & out["indicator"].str.contains("Gemiddelde", na=False)).any()


def test_overdispersion_makes_verdicts_conservative():
    import numpy as np
    from pipeline.quality import funnel_verdicts
    rng = np.random.default_rng(1)
    n = 60
    # true rates vary between hospitals (overdispersion) around 5%, big samples
    true = np.clip(rng.normal(0.05, 0.015, n), 0.001, 0.2)
    den = pd.Series(np.full(n, 2000.0))
    y = pd.Series(rng.binomial(2000, true) / 2000)
    se = (0.05 * 0.95 / den) ** 0.5
    naive_worse = ((y - 0.05) > 1.96 * se).sum()
    verdicts = funnel_verdicts(y, se, 0.05, "lower_better")
    assert (verdicts == "slechter").sum() < naive_worse / 3   # most 'significant' differences are ordinary spread
    assert (verdicts == "beter").sum() >= (verdicts == "slechter").sum()  # positive signal needs less evidence
    extreme = funnel_verdicts(pd.concat([y, pd.Series([0.30])], ignore_index=True),
                              pd.concat([se, pd.Series([se.iloc[0]])], ignore_index=True), 0.05, "lower_better")
    assert extreme.iloc[-1] == "slechter"  # a real outlier is still flagged



# --- regressions from the statistical review ---------------------------------------------------

def _interval_rows(loc, point, lo, hi, n, kind="prom", year="2025"):
    base = ("Verschilscore tussen heup PROM preoperatief en 12 maanden na ingreep. OHS som score. " if kind == "prom"
            else "Gecorrigeerd percentage revisie binnen 1 jaar na primaire THP. ")
    roles = [("Gemiddelde" if kind == "prom" else "Gecorrigeerd percentage", point),
             ("95% Betrouwbaarheidsinterval Lower bound", lo), ("95% Betrouwbaarheidsinterval Upper bound", hi)]
    if n is not None:
        roles.append(("Aantal (N)", n))
    return [{"procedure_id": "heup", "location_key": loc, "verslagjaar": year, "indicator": base + s,
             "value": str(v), "numerator": None, "denominator": None} for s, v in roles]


def test_placeholders_small_n_and_implausible_values_are_not_judged():
    rows = []
    for i in range(12):
        rows += _interval_rows(f"h{i}", 18 + (i % 3), 17 + (i % 3), 19 + (i % 3), 100)
    rows += _interval_rows("zero", 0, 0, 0, 0)            # placeholder: dropped
    rows += _interval_rows("tiny", 40, 39, 41, 4)         # n < 20: not judged
    rows += _interval_rows("crazy", 2364, 2357, 2371, 300)  # impossible change on a 0-48 scale
    out = compare(pd.DataFrame(rows))
    by = out[out["method"] == "interval"].set_index("location_key")
    assert "zero" not in by.index
    assert pd.isna(by.loc["tiny", "verdict"]) and "patiënten" in by.loc["tiny", "position"]
    assert pd.isna(by.loc["crazy", "verdict"]) and "onwaarschijnlijk" in by.loc["crazy", "position"]
    assert by.loc["h0", "national_rate"] == pytest.approx(19)  # median of real hospitals only


def test_swapped_bounds_are_repaired():
    rows = _interval_rows("s", 1.0, 2.0, 0.5, None, kind="rev")
    out = compare(pd.DataFrame(rows))
    r = out[out["method"] == "interval"].iloc[0]
    assert r["ci_low"] == 0.5 and r["ci_high"] == 2.0 and pd.isna(r["position"])


def test_ratio_not_judged_when_few_hospitals_publish_counts():
    rows = [{"procedure_id": "heup", "indicator": "Diepe wondinfectie complicatie", "location_key": f"l{i}",
             "verslagjaar": "2025", "numerator": 1 if i < 3 else None, "denominator": 100 if i < 3 else None,
             "value": "1.0"} for i in range(10)]
    out = compare(pd.DataFrame(rows))
    assert out["verdict"].isna().all() and out["position"].str.contains("teller").all()


def test_rare_events_are_not_flagged_on_tiny_numbers():
    rows = [{"procedure_id": "heup", "indicator": "Diepe wondinfectie complicatie", "location_key": f"l{i}",
             "verslagjaar": "2025", "numerator": 2, "denominator": 250, "value": None} for i in range(30)]
    rows.append({"procedure_id": "heup", "indicator": "Diepe wondinfectie complicatie", "location_key": "small",
                 "verslagjaar": "2025", "numerator": 2, "denominator": 42, "value": None})
    out = compare(pd.DataFrame(rows)).set_index("location_key")
    assert out.loc["small", "verdict"] == "gemiddeld"  # 2/42 is not convincing evidence of worse care


def test_single_prom_scale_does_not_make_a_hospital_better():
    from pipeline.quality import domain_verdicts
    one = pd.DataFrame({"indicator_nl": ["Verbetering volgens patiënt na 12 maanden: algemene gezondheid",
                                         "Verbetering volgens patiënt na 12 maanden: functie van de heup"],
                        "verdict": ["beter", "gemiddeld"]})
    assert domain_verdicts(one)["herstel"] == "gemiddeld"
    specific = one.assign(verdict=["gemiddeld", "beter"])
    assert domain_verdicts(specific)["herstel"] == "beter"


def test_line_parser_reads_label_tables_without_separators():
    text = ("Overzicht contracten zorgverzekeraars 2027\nVerzekeraar Label Status\n"
            "DSW DSW Gecontracteerd\nVGZ Univé In onderhandeling\nDitzo (Ik Kies Zelf ASR) Gecontracteerd\n"
            "Zilveren Kruis Zilveren Kruis Gecontracteerd met omzetplafond\n"
            "Heeft u een polis bij een verzekeraar waarmee wij geen contract hebben, dan betaalt u mogelijk zelf bij.\n"
            "* In dit overzicht staat de situatie van 03-11-2026.")
    rows = contracts_parse.parse_lines(text)
    got = {(r["concern"], r["label"]): (r["status"], r["omzetplafond"]) for r in rows}
    assert got[("VGZ", "Univé")] == ("in_onderhandeling", None)
    assert got[("a.s.r.", "Ik kies zelf")][0] == "gecontracteerd"
    assert got[("Achmea", "Zilveren Kruis")] == ("gecontracteerd", True)
    assert ("DSW", None) in got  # only 'DSW' named: concern-wide
    assert len(rows) == 4  # the prose sentence is not a contract row
    assert contracts_parse.find_peildatum(text) == "03-11-2026"


def test_legend_coded_overview():
    text = ("Overzicht zorgverzekeraars en contracten 2027\n0: wij hebben geen contract\n"
            "1: we hebben aan elkaar een voorstel voor 2027 uitgebracht\n4: we hebben een contract\n"
            "Merklabel\nZorgverzekeraar\nContract 2027\nContract 2026\n"
            "Anderzorg\nMenzis\n4\n4\nBewuzt\nVGZ\n1\n4\nOHRA\nCZ\n0\n4\n")
    got = {(r["concern"], r["label"]): r["status"] for r in contracts_parse.parse_legend(text)}
    assert got[("VGZ", "Bewuzt")] == "in_onderhandeling"
    assert got[("CZ", "OHRA")] == "geen_contract"
    assert any(k[0] == "Menzis" and v == "gecontracteerd" for k, v in got.items())


def test_icon_alt_text_is_kept():
    from scrapers.contracts import html_to_text
    text = html_to_text('<div>Zilveren Kruis <img src="x.svg" alt="Gecontracteerd"></div><div>CZ <span aria-label="In onderhandeling"></span></div>')
    assert "Zilveren Kruis  Gecontracteerd" in text.replace("\n", " ") or "Gecontracteerd" in text
    rows = {r["concern"]: r["status"] for r in contracts_parse.parse_lines(text.replace("\n", " \n"))}
    assert rows.get("Achmea") == "gecontracteerd" and rows.get("CZ") == "in_onderhandeling"


def test_care_type_matrix_uses_hospital_column_and_ambiguous_marks():
    text = ("Gecontracteerd voor 2027\n✓\nOp peildatum voor 2027 nog geen volledige overeenstemming\n✓\n"
            "Op peildatum niet gecontracteerd voor 2027\n✗\n")
    table = [["Verzekeraar", "Labels", "Ziekenhuis", "GGz", "Wijkverpleging"],
             ["CZ", "CZ", "✓", "✗", "✗"],
             ["VGZ", "VGZ", "✗", "✓", "✓"]]
    rows = {r["concern"]: r["status"] for r in contracts_parse.parse_source([table], text)}
    assert rows.get("VGZ") == "geen_contract"   # hospital column says 'niet gecontracteerd'
    assert "CZ" not in rows                      # '✓' means contracted OR not yet agreed: no claim


def test_mark_matrix_without_known_columns_makes_no_claim():
    rows = contracts_parse.parse_tables([[["CZ", "CZ", "✓", "✓", "✗", "✗"]]])
    assert rows == []


def test_policy_overview_counts_reimbursed_better_hospitals():
    from pipeline.score import policy_overview
    near = pd.DataFrame({"organisatie_agb": ["A", "B", "C"], "quality_verdict": ["boven_gemiddeld", "boven_gemiddeld", "gemiddeld"]})
    contracts = pd.DataFrame([
        {"organisatie_agb": "A", "concern": "VGZ", "label": None, "status": "gecontracteerd", "peildatum": "2026-11-15"},
        {"organisatie_agb": "B", "concern": "VGZ", "label": None, "status": "geen_contract", "peildatum": "2026-11-15"},
    ])
    policies = pd.DataFrame([
        {"concern": "VGZ", "label": "VGZ", "polis": "Basis Keuze", "polis_type": "budget", "premie_per_maand": "167.40", "vergoeding_niet_gecontracteerd_pct": "70"},
        {"concern": "VGZ", "label": "VGZ", "polis": "Eigen Keuze", "polis_type": "combinatie", "premie_per_maand": "188.15", "vergoeding_niet_gecontracteerd_pct": "100"},
        {"concern": "CZ", "label": "CZ", "polis": "Zorgbewust", "polis_type": "budget", "premie_per_maand": "176.25", "vergoeding_niet_gecontracteerd_pct": None},
    ])
    out = policy_overview(near, contracts, policies).set_index("polis")
    assert (out.loc["Eigen Keuze", ["volledig", "vrij", "deels", "onbekend"]] == [1, 1, 0, 0]).all()
    assert (out.loc["Basis Keuze", ["volledig", "deels", "onbekend"]] == [1, 1, 0]).all()
    assert (out.loc["Zorgbewust", ["volledig", "deels", "onbekend"]] == [0, 0, 2]).all()
    assert out.index[0] == "Eigen Keuze"


def test_zorgkaart_parse_and_link():
    from pipeline.reviews_ingest import link
    from scrapers.zorgkaart import parse_institution
    html = ('<script type="application/ld+json">{"@type":"Hospital","name":"UMC Utrecht",'
            '"address":{"postalCode":"3584 CX","addressLocality":"Utrecht"},'
            '"aggregateRating":{"@type":"AggregateRating","ratingValue":8.4,"ratingCount":1234}}</script>')
    row = parse_institution(html, "https://example/zorginstelling/ziekenhuis-umc-utrecht-utrecht-1")
    assert row["rating"] == 8.4 and row["count"] == 1234 and row["postcode"] == "3584CX"
    locations = pd.DataFrame([
        {"location_key": "06020602-3584CX", "locatie_naam": "UMC Utrecht", "organisatie_naam": "UMC Utrecht", "postcode": "3584CX", "plaats": "Utrecht"},
        {"location_key": "06010618-3582KE", "locatie_naam": "Diakonessenhuis", "organisatie_naam": "Diak", "postcode": "3582KE", "plaats": "Utrecht"},
    ])
    linked = link(pd.DataFrame([{**row, "fetched_on": "2026-11-25"}]), locations)
    assert linked.iloc[0]["location_key"] == "06020602-3584CX"


def test_explain_in_plain_words():
    from pipeline.explain import explain, trend_sentences
    title, measured, (css, verdict) = explain({"indicator": "Heroperatie (revisie) binnen 1 jaar", "rate": 1.81,
                                               "national_rate": 0.64, "method": "interval", "verdict": "gemiddeld"})
    assert title == "Heroperatie binnen 1 jaar" and "1,8 op de 100" in measured and "landelijk 0,6" in measured
    assert "te weinig patiënten" in verdict
    title, measured, (css, verdict) = explain({"indicator": "Verbetering volgens patiënt na 12 maanden: pijn bij bewegen",
                                               "rate": 5.75, "national_rate": 5.85, "method": "interval", "verdict": "gemiddeld"})
    assert "daalde met 5,8 punten (schaal 0 tot 10)" in measured and verdict == "rond het gemiddelde"
    _, measured, (css, verdict) = explain({"indicator": "Diepe wondinfectie binnen 90 dagen", "rate": 0.0,
                                           "national_rate": 0.0078, "method": "ratio", "verdict": "beter"})
    assert "0,0 op de 100" in measured and css == "beter"
    trend = pd.DataFrame({"indicator": ["Diepe wondinfectie binnen 90 dagen"] * 3, "verslagjaar": [2023, 2024, 2025],
                          "verdict": ["beter"] * 3})
    assert trend_sentences(trend) == ["Al 3 jaar beter dan gemiddeld op: diepe wondinfectie binnen 90 dagen"]


CZ_PAGE = """Resultaten van 2027 :
3 zorgverleners
Umc Utrecht Heidelberglaan 100
4,0 km - 4,0 kilometer van je locatie Utrecht, Heidelberglaan 100
(Nog) geen contract: wel vergoed
Met omzetplafond
Reviews: 8,0 op basis van 85 waarderingen voor Reviews 8 , 0 85 reviews
St. Antonius Ziekenhuis Locatie Utrecht Soestwetering 1
4,6 km - 4,6 kilometer van je locatie Utrecht, Soestwetering 1
Nog geen contract: een deel niet vergoed
Stichting Alexander Monro Ziekenhuis Professor Bronkhorstlaan 10g 94
9,0 km - 9,0 kilometer van je locatie Bilthoven, Professor Bronkhorstlaan 10g 94
Contract: vergoed
UMC Utrecht, loc. Alexander Monro Ziekenhuis Professor Bronkhorstlaan 10
9,0 km - 9,0 kilometer van je locatie Bilthoven, Professor Bronkhorstlaan 10
(Nog) geen contract: wel vergoed
"""


def test_cz_finder_parse_and_link():
    from pipeline.insurer_contracts import match_entries, per_organisation
    from scrapers.cz_zorgvinder import parse_results
    entries, total = parse_results(CZ_PAGE)
    assert total == 3 and len(entries) == 4
    assert entries[0] == {"name": "Umc Utrecht", "address": "Heidelberglaan 100", "city": "Utrecht",
                          "status": "vergoed_als_contract", "omzetplafond": True}
    assert entries[1]["status"] == "in_onderhandeling" and entries[1]["omzetplafond"] is False
    assert entries[2]["status"] == "gecontracteerd"
    locations = pd.DataFrame([
        {"location_key": "06020602-3584CX", "organisatie_agb": "06020602", "organisatie_naam": "UMC Utrecht",
         "locatie_naam": "UMC Utrecht", "huisnummer": "100", "plaats": "UTRECHT"},
        {"location_key": "06010618-3582KE", "organisatie_agb": "06010618", "organisatie_naam": "Diakonessenhuis",
         "locatie_naam": "Diakonessenhuis Utrecht", "huisnummer": "1", "plaats": "Utrecht"},
        {"location_key": "22220330-3723MB", "organisatie_agb": "22220330", "organisatie_naam": "Alexander Monro Ziekenhuis",
         "locatie_naam": "Alexander Monro Ziekenhuis", "huisnummer": "10", "plaats": "Bilthoven"},
    ])
    df = pd.DataFrame(entries).assign(concern="CZ", label="CZ", year=2027, source="CZ zorgvinder",
                                      fetched_on="2026-11-25", source_url="u")
    matched = match_entries(df, locations)
    assert matched["location_key"].tolist()[0] == "06020602-3584CX"
    assert pd.isna(matched["location_key"].iloc[1])  # same house number, other hospital: no match
    assert matched["location_key"].iloc[2] == "22220330-3723MB"
    assert pd.isna(matched["location_key"].iloc[3])  # UMC clinic in the same building keeps off
    orgs = per_organisation(matched).set_index("organisatie_agb")
    assert orgs.loc["22220330", "status"] == "gecontracteerd"
    assert orgs.loc["06020602", "status"] == "vergoed_als_contract" and bool(orgs.loc["06020602", "omzetplafond"])


def test_insurer_finder_wins_over_hospital_page_and_counts_as_reimbursed(tmp_path, monkeypatch):
    from pipeline import score
    pd.DataFrame([{"year": 2027, "organisatie_agb": "06020602", "concern": "CZ", "label": "CZ",
                   "status": "vergoed_als_contract", "peildatum": "2026-11-25"}]).to_csv(tmp_path / "contracts_insurer.csv", index=False)
    pd.DataFrame([{"year": 2027, "organisatie_agb": "06020602", "concern": "CZ", "label": "CZ",
                   "status": "in_onderhandeling", "peildatum": "2026-11-01"},
                  {"year": 2027, "organisatie_agb": "06020602", "concern": "VGZ", "label": "",
                   "status": "in_onderhandeling", "peildatum": "2026-11-01"}]).to_csv(tmp_path / "contracts_candidates.csv", index=False)
    monkeypatch.setattr(score, "PROCESSED", tmp_path)
    monkeypatch.setattr(score, "MANUAL", tmp_path)
    contracts = score.load_contracts(2027)
    cz = score.contract_for(contracts, "06020602", "CZ", "CZ")
    assert cz["status"] == "vergoed_als_contract" and cz["origin"] == "verzekeraar"
    near = pd.DataFrame({"organisatie_agb": ["06020602"], "quality_verdict": ["boven_gemiddeld"]})
    policies = pd.DataFrame([
        {"concern": "CZ", "label": "CZ", "polis": "Zorgbewust", "polis_type": "budget", "premie_per_maand": "170", "vergoeding_niet_gecontracteerd_pct": "65"},
        {"concern": "VGZ", "label": "VGZ", "polis": "Basis Keuze", "polis_type": "budget", "premie_per_maand": "167", "vergoeding_niet_gecontracteerd_pct": "70"},
    ])
    out = score.policy_overview(near, contracts, policies).set_index("polis")
    assert out.loc["Zorgbewust", "volledig"] == 1
    # a hospital saying 'in talks' does not tell what the insurer pays meanwhile: unknown, not 'partly'
    assert out.loc["Basis Keuze", "onbekend"] == 1


def test_postcode_fallback_without_pdok(tmp_path):
    from pipeline.geo import approximate_from_cache
    cache = tmp_path / "c.csv"
    pd.DataFrame([{"postcode": "3584CX", "huisnummer": "100", "lat": 52.08, "lon": 5.18},
                  {"postcode": "3582KE", "huisnummer": "1", "lat": 52.09, "lon": 5.13}]).to_csv(cache, index=False)
    assert approximate_from_cache("3584 AB", cache) == (52.08, 5.18)
    assert approximate_from_cache("3583", cache) is not None  # nearest PC4 number
    assert approximate_from_cache("9999", cache) is None


def test_premium_amounts_found_in_insurer_text():
    from scrapers.verify_premiums import amount_text, find_amounts
    amounts = {"Basis Start": amount_text(159.45), "Basis Zeker": amount_text(164.95), "Exclusief": amount_text(186.9)}
    text = "Premies 2027\nBasis Start € 159,45 per maand\nBasis Zeker €\n164,95\nExclusief 1186,90"
    assert find_amounts(text, amounts) == {"Basis Start", "Basis Zeker"}  # 1186,90 is not 186,90


def test_policies_in_scope_come_from_the_insurer_itself():
    """Direct sources only: every policy the app shows is sourced on the insurer's own domain."""
    from pipeline.reference import scope
    from pipeline.score import load_policies
    from scrapers.verify_premiums import SITES, site_of
    policies = load_policies(2027)
    assert set(policies["label"]) == set(scope()["label"])
    for p in policies.itertuples():
        own = site_of(SITES[p.label]).split(".")[-2]  # e.g. 'vgz' also allows cooperatievgz.nl
        assert own in site_of(p.source_url), (p.label, p.polis, p.source_url)
