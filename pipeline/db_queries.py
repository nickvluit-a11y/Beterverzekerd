"""Queries the app and reports run against the DuckDB database (see pipeline/build_db.py)."""

from __future__ import annotations

import duckdb
import pandas as pd


def has_quality_data(con: duckdb.DuckDBPyConnection) -> bool:
    return con.execute("SELECT count(*) FROM measurements").fetchone()[0] > 0


def locations_for_procedure(con: duckdb.DuckDBPyConnection, procedure_id: str) -> pd.DataFrame:
    """Locations with coordinates that still report the procedure (active in v_quality_latest)."""
    return con.execute("""
        SELECT l.*, coalesce(l.locatie_naam, l.organisatie_naam) || ' (' || coalesce(l.plaats, '') || ')' AS location_name
        FROM locations l
        WHERE l.lat IS NOT NULL
          AND l.location_key IN (SELECT location_key FROM v_quality_latest WHERE procedure_id = ?)
    """, [procedure_id]).df()


def quality_latest(con: duckdb.DuckDBPyConnection, procedure_id: str) -> pd.DataFrame:
    return con.execute("SELECT * FROM v_quality_latest WHERE procedure_id = ?", [procedure_id]).df()


def indicator_profile(con: duckdb.DuckDBPyConnection, location_key: str, procedure_id: str) -> pd.DataFrame:
    """The year of the current verdict: each indicator for this location next to the national rate."""
    return con.execute("""
        WITH latest AS (
            SELECT verslagjaar AS y FROM v_quality_latest WHERE location_key = ? AND procedure_id = ?)
        SELECT q.indicator_code, coalesce(q.indicator_nl, i.thema) AS indicator, i.indicator_naam, i.eenheid,
               i.indicator_type, q.verslagjaar, q.method, q.direction, q.rate, q.ci_low, q.ci_high,
               q.national_rate, q.verdict, q.position, q.numerator,
               coalesce(q.denominator, q.n_waarnemingen) AS denominator, q.value
        FROM quality_indicator q JOIN latest ON q.verslagjaar = latest.y
        LEFT JOIN indicators i USING (indicator_code)
        WHERE q.location_key = ? AND q.procedure_id = ?
        ORDER BY (q.verdict IS NULL), q.method, indicator
    """, [location_key, procedure_id, location_key, procedure_id]).df()


def indicator_trend(con: duckdb.DuckDBPyConnection, location_key: str, procedure_id: str) -> pd.DataFrame:
    """Every judged or mean-score indicator over the years, with the national rate per year."""
    return con.execute("""
        SELECT q.verslagjaar, coalesce(q.indicator_nl, i.thema) AS indicator, q.indicator_code,
               q.rate, q.national_rate, q.verdict, q.method
        FROM quality_indicator q LEFT JOIN indicators i USING (indicator_code)
        WHERE q.location_key = ? AND q.procedure_id = ? AND q.method IS NOT NULL
        ORDER BY indicator, q.verslagjaar
    """, [location_key, procedure_id]).df()


def latest_judged(con: duckdb.DuckDBPyConnection, procedure_id: str) -> pd.DataFrame:
    """Judged indicators in the year of each location's current verdict (for plain-language highlights)."""
    return con.execute("""
        SELECT q.location_key, q.verslagjaar, q.indicator_nl, q.verdict
        FROM quality_indicator q JOIN v_quality_latest v USING (location_key, procedure_id, verslagjaar)
        WHERE q.procedure_id = ? AND q.verdict IN ('beter', 'slechter', 'gemiddeld')
    """, [procedure_id]).df()
