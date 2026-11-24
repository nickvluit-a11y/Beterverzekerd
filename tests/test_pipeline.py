"""Tests on synthetic data. They check the logic, not the real file layouts (unknown until CI downloads them)."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from pipeline import contracts_parse, nza_ingest, zorginzicht_ingest
from pipeline.contract_status import normalise_status
from pipeline.geo import clean_postcode, parse_point
from pipeline.reference import match_label, match_location, normalise
from pipeline.score import access_status, contract_for, haversine_km, hospitals_within, overview
from scrapers.common import find_links, safe_filename
from scrapers.nza_wachttijden import pick_latest


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
    (raw / "meta.json").write_text(json.dumps({"results": {"avl": {"url": "https://example.org/x.pdf"}}}))
    (raw / "avl.txt").write_text("Contracten 2027. Peildatum 01-11-2026")
    (raw / "avl.tables.json").write_text(json.dumps([[["CZ", "Gecontracteerd"]]]))
    monkeypatch.setattr(contracts_parse, "PROCESSED", tmp_path / "out")
    assert contracts_parse.main([str(raw)]) == 0
    out = pd.read_csv(tmp_path / "out" / "contracts_candidates.csv")
    assert out.loc[0, "concern"] == "CZ" and out.loc[0, "year"] == 2027 and out.loc[0, "peildatum"] == "01-11-2026"


# --- scraper helpers -----------------------------------------------------------------------

def test_find_links_and_latest_version():
    html = ('<a href="/PUC/Handlers/DownloadDocument.ashx?identifier=PUC_651798_22&amp;versienummer=3&amp;type=csv">csv</a>'
            '<a href="/PUC/Handlers/DownloadDocument.ashx?identifier=PUC_651798_22&amp;versienummer=12&amp;type=csv">csv</a>'
            '<a href="/other.pdf">pdf</a>')
    links = find_links(html, "https://puc.overheid.nl/nza/doc/PUC_651798_22/", r"DownloadDocument\.ashx.*type=csv")
    assert len(links) == 2 and all(link.startswith("https://puc.overheid.nl/PUC/") for link in links)
    assert "versienummer=12" in pick_latest(links)


def test_safe_filename():
    assert safe_filename("https://x.nl/a/Open%20data.xlsx") == "Open_20data.xlsx"
    assert safe_filename("https://x.nl/dl", 'attachment; filename="MSZ 2025.xlsx"') == "MSZ_2025.xlsx"


# --- ingest on synthetic files -------------------------------------------------------------

def test_zorginzicht_ingest(tmp_path, monkeypatch):
    raw = tmp_path / "2026-11-24"
    raw.mkdir()
    df = pd.DataFrame({
        "Verslagjaar": ["2025"] * 4,
        "AGB-code": ["", "", "", ""],
        "Naam instelling": ["Meander Medisch Centrum", "UMC Utrecht", "Meander Medisch Centrum", "Onbekend Ziekenhuis"],
        "Indicatorset": ["Heupprothese (THP)", "Cataract", "Borstkanker", "Knieprothese (TKP)"],
        "Indicator": ["Revisie binnen 1 jaar", "Complicaties", "Irrelevant", "Revisie binnen 1 jaar"],
        "Teller": ["3", "1", "5", "2"],
        "Noemer": ["400", "900", "50", "300"],
    })
    df.to_excel(raw / "msz_2025.xlsx", index=False)
    monkeypatch.setattr(zorginzicht_ingest, "PROCESSED", tmp_path / "out")
    monkeypatch.setattr(zorginzicht_ingest, "INVENTORY", tmp_path / "inventory.md")
    assert zorginzicht_ingest.main([str(raw)]) == 0
    out = pd.read_csv(tmp_path / "out" / "quality.csv")
    assert sorted(out["procedure_id"]) == ["heup", "knie", "staar"]
    assert out.set_index("procedure_id").loc["heup", "location_id"] == "meander"
    assert pd.isna(out.set_index("procedure_id").loc["knie", "location_id"])
    assert "Naam instelling" in (tmp_path / "inventory.md").read_text()


def test_nza_ingest(tmp_path, monkeypatch):
    raw = tmp_path / "2026-11-24"
    raw.mkdir()
    (raw / "wachttijden.csv").write_text(
        "PEILDATUM;NAAM_LOCATIE;PLAATS;AGB_LOCATIE;KVK_INSTELLING;SPECIALISME;TYPE_WACHTTIJD;WACHTTIJD\n"
        "2026-09-15;Meander Medisch Centrum;Amersfoort;;123;Orthopedie;Behandeling;7\n"
        "2026-09-15;UMC Utrecht;Utrecht;;456;Oogheelkunde;Polikliniek;4,5\n"
        "2026-09-15;UMC Utrecht;Utrecht;;456;Cardiologie;Polikliniek;3\n",
        encoding="utf-8")
    monkeypatch.setattr(nza_ingest, "PROCESSED", tmp_path / "out")
    monkeypatch.setattr(nza_ingest, "INVENTORY", tmp_path / "inventory.md")
    assert nza_ingest.main([str(raw)]) == 0
    out = pd.read_csv(tmp_path / "out" / "waiting_times.csv")
    # orthopedics feeds both hip and knee, ophthalmology feeds cataract; cardiology dropped
    assert sorted(out["procedure_id"]) == ["heup", "knie", "staar"]
    assert out.loc[out["procedure_id"] == "staar", "weeks"].iloc[0] == 4.5
    assert set(out["location_id"]) == {"meander", "umcu"}


# --- scoring -------------------------------------------------------------------------------

def test_haversine_and_radius():
    assert haversine_km(52.0907, 5.1214, 52.3676, 4.9041) == pytest.approx(34, abs=2)  # Utrecht–Amsterdam
    near = hospitals_within(52.0870, 5.1790, 10)
    assert near.iloc[0]["location_id"] == "umcu"
    assert "jbz" not in set(near["location_id"])


def test_contract_for_prefers_label_then_concern_and_latest():
    contracts = pd.DataFrame([
        {"location_id": "umcu", "concern": "CZ", "label": None, "status": "geen_contract", "peildatum": "2026-11-01"},
        {"location_id": "umcu", "concern": "CZ", "label": None, "status": "gecontracteerd", "peildatum": "2026-12-01"},
        {"location_id": "umcu", "concern": "CZ", "label": "OHRA", "status": "in_onderhandeling", "peildatum": "2026-11-15"},
    ])
    assert contract_for(contracts, "umcu", "CZ", "CZ")["status"] == "gecontracteerd"
    assert contract_for(contracts, "umcu", "CZ", "OHRA")["status"] == "in_onderhandeling"
    assert contract_for(contracts, "umcu", "VGZ", "VGZ") is None


def test_access_status():
    assert access_status({"polis_type": "Restitutie"}, None) == "gecontracteerd"
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
        {"procedure_id": "heup", "location_id": "umcu", "weeks": 9, "wait_type": "Behandeling", "peildatum": "2026-09-15"},
        {"procedure_id": "heup", "location_id": "diak_utr", "weeks": 5, "wait_type": "Behandeling", "peildatum": "2026-09-15"},
        {"procedure_id": "heup", "location_id": "diak_utr", "weeks": 2, "wait_type": "Polikliniek", "peildatum": "2026-09-15"},
    ])
    quality = pd.DataFrame([
        {"procedure_id": "heup", "location_id": "umcu", "indicator": "a", "verslagjaar": "2025"},
        {"procedure_id": "heup", "location_id": "umcu", "indicator": "b", "verslagjaar": "2025"},
    ])
    summary, detail = overview(52.0870, 5.1790, "heup", radius_km=6, policies=policies,
                               contracts=contracts, waits=waits, quality=quality)
    cz = summary.set_index("polis").loc["CZ Zorgbewust"]
    assert cz["gecontracteerd"] == 1 and cz["met_omzetplafond"] == 1
    assert cz["kortste_wachttijd_gecontracteerd_weken"] == 5  # treatment wait, not outpatient
    vgz = summary.set_index("polis").loc["VGZ Ruime Keuze"]
    assert vgz["onbekend"] == 0  # restitutie covers all
    umcu = detail[(detail["polis"] == "CZ Zorgbewust") & (detail["location"] == "UMC Utrecht Heidelberglaan")].iloc[0]
    assert umcu["quality_indicators"] == 2


def test_overview_without_policy_file_falls_back_to_labels():
    summary, _ = overview(52.0870, 5.1790, "heup", radius_km=6, contracts=pd.DataFrame(),
                          waits=pd.DataFrame(), quality=pd.DataFrame())
    assert len(summary) > 20 and summary["onbekend"].gt(0).all()


# --- geo -----------------------------------------------------------------------------------

def test_postcode_helpers():
    assert clean_postcode("3584 cx") == "3584CX"
    assert clean_postcode("3584") == "3584"
    assert clean_postcode("ABCD") is None
    assert parse_point("POINT(5.179 52.087)") == (52.087, 5.179)
