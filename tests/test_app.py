"""Smoke test of the Streamlit app with geocoding stubbed out (no network in tests)."""

from streamlit.testing.v1 import AppTest

import pipeline.geo


def test_app_renders_overview(monkeypatch):
    monkeypatch.setattr(pipeline.geo, "geocode_postcode", lambda code: (52.0870, 5.1790))
    at = AppTest.from_file("../app/app.py", default_timeout=30)
    at.run()
    assert not at.exception
    at.button[0].click().run()
    assert not at.exception
    assert len(at.dataframe) == 2  # per-policy table and detail table
    assert at.dataframe[0].value.shape[0] > 20  # falls back to one row per label


def test_app_rejects_bad_postcode(monkeypatch):
    monkeypatch.setattr(pipeline.geo, "geocode_postcode", lambda code: (52.0870, 5.1790))
    at = AppTest.from_file("../app/app.py", default_timeout=30)
    at.run()
    at.text_input[0].set_value("hallo")
    at.button[0].click().run()
    assert at.error and "geldige postcode" in at.error[0].value
