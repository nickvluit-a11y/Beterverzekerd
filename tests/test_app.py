"""Smoke tests of the Streamlit app with geocoding stubbed out (no network in tests)."""

from streamlit.testing.v1 import AppTest

import pipeline.geo


def _app(monkeypatch):
    monkeypatch.setattr(pipeline.geo, "locate", lambda code: (52.0870, 5.1790))
    at = AppTest.from_file("../app/app.py", default_timeout=240)
    at.run()
    return at


def test_app_renders_search_results(monkeypatch):
    at = _app(monkeypatch)
    assert not at.exception
    at.button[0].click().run()
    assert not at.exception
    assert any("ziekenhuizen" in m.value for m in at.markdown)


def test_app_rejects_bad_postcode(monkeypatch):
    at = _app(monkeypatch)
    at.text_input[0].set_value("hallo")
    at.button[0].click().run()
    assert at.error and "postcode" in at.error[0].value


def test_app_brand_of_a_group_follows_main_brand(monkeypatch):
    at = _app(monkeypatch)
    insurer = next(s for s in at.selectbox if s.label == "Bij wie ben je verzekerd?")
    options = list(insurer.options)  # shown text, e.g. 'OHRA (onderdeel van CZ)'
    assert "OHRA (onderdeel van CZ)" in options and not any(o.startswith("ONVZ") for o in options)
    insurer.set_value("OHRA")
    at.button[0].click().run()
    assert not at.exception
    text = " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)
    assert "OHRA" in text and "Zorgkaart" not in text
