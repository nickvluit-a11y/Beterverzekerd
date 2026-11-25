"""Build the DuckDB database from the linked CSV tables (CSV in git stays the source of truth).

    python -m pipeline.build_db            -> data/beterverzekerd.duckdb

Tables
  locations            every MSZ location (key: location_key = organisation AGB + postcode)
  hospitals_manual     hand-made enrichment: contract page per organisation, aliases
  indicators           indicator catalogue + our judgement rules (direction, label)
  measurements         location × indicator × verslagjaar (hip, knee, cataract)
  quality_indicator    each measurement compared with the national rate (Wilson 95%)
  quality_location     per location × procedure × verslagjaar: better / worse / average counts + verdict
  contracts            checked contract status per organisation × concern/label (with peildatum history)
  contract_candidates  parsed but not yet checked
  waiting_times        NZa (when available)
  labels               label -> concern
Views
  v_national           national rate per indicator × year
  v_quality_latest     current verdict per active location × procedure (see the view)
  v_quality_trend      verdict per location × procedure over the years
  v_integrity          linkage problems (rows that do not join); must stay empty or explained
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd

from pipeline.quality import compare, direction_for, hospital_verdict, with_catalogue
from pipeline.reference import MANUAL, PROCESSED, REFERENCE, ROOT, procedures

DB_PATH = ROOT / "data" / "beterverzekerd.duckdb"


def _csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str) if path.exists() else pd.DataFrame()


def _num(df: pd.DataFrame, *cols: str) -> pd.DataFrame:
    for col in cols:
        if col in df:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    return df


def load_frames() -> dict[str, pd.DataFrame]:
    locations = _csv(REFERENCE / "locations.csv")
    if locations.empty:
        locations = _csv(REFERENCE / "locations_zorginzicht.csv")
    locations = _num(locations, "lat", "lon", "first_year", "last_year")

    indicators = _csv(REFERENCE / "indicators.csv")
    if not indicators.empty:
        rules = [direction_for(p, f"{t or ''} | {n or ''}", code)
                 for p, t, n, code in zip(indicators["procedure_id"], indicators.get("thema"),
                                          indicators.get("indicator_naam"), indicators["indicator_code"])]
        indicators["direction"] = [r[0] for r in rules]
        indicators["label_nl"] = [r[1] for r in rules]

    measurements = _num(_csv(PROCESSED / "measurements.csv"), "verslagjaar", "numerator", "denominator", "n_waarnemingen")
    return {
        "locations": locations,
        "hospitals_manual": _csv(MANUAL / "hospitals.csv"),
        "indicators": indicators,
        "measurements": measurements,
        "contracts": _csv(MANUAL / "contracts.csv"),
        "contract_candidates": _csv(PROCESSED / "contracts_candidates.csv"),
        "waiting_times": _num(_csv(PROCESSED / "waiting_times.csv"), "weeks"),
        "labels": _csv(MANUAL / "concerns_labels.csv"),
        "procedures": procedures().astype(str),
    }


def quality_tables(measurements: pd.DataFrame, indicators: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(quality_indicator, quality_location) for every verslagjaar, so quality can be followed over time."""
    if measurements.empty or indicators.empty:
        return pd.DataFrame(), pd.DataFrame()
    compared = compare(with_catalogue(measurements, indicators))
    per_year = []
    for (proc, year), group in compared.groupby(["procedure_id", "verslagjaar"]):
        verdicts = hospital_verdict(group, proc)
        verdicts.insert(1, "procedure_id", proc)
        verdicts["verslagjaar"] = year
        per_year.append(verdicts)
    keep = ["location_key", "procedure_id", "indicator_code", "verslagjaar", "direction", "indicator_nl",
            "value", "numerator", "denominator", "n_waarnemingen", "rate", "ci_low", "ci_high", "national_rate",
            "method", "verdict", "position", "source"]
    quality_indicator = compared[[c for c in keep if c in compared]]
    return quality_indicator, (pd.concat(per_year, ignore_index=True) if per_year else pd.DataFrame())


VIEWS = """
CREATE OR REPLACE VIEW v_national AS
SELECT procedure_id, indicator_code, verslagjaar,
       sum(numerator) / nullif(sum(denominator), 0) AS national_rate,
       count(*) FILTER (WHERE denominator > 0) AS providers
FROM measurements
WHERE denominator > 0 AND numerator BETWEEN 0 AND denominator
GROUP BY ALL;

-- The current verdict per location x procedure, one definition for the whole app:
--   * active: the location reported the procedure in the newest or the year before (national), so
--     locations that stopped (closed, merged, AGB reused) are not shown with an old verdict;
--   * the verdict comes from the newest of those two years that has one; else 'geen_data'.
CREATE OR REPLACE VIEW v_quality_latest AS
WITH newest AS (SELECT procedure_id, max(verslagjaar) AS y FROM quality_location GROUP BY procedure_id),
recent AS (
    SELECT q.* FROM quality_location q JOIN newest n USING (procedure_id) WHERE q.verslagjaar >= n.y - 1)
SELECT * FROM recent
QUALIFY row_number() OVER (PARTITION BY location_key, procedure_id
                           ORDER BY (quality_verdict = 'geen_data'), verslagjaar DESC) = 1;

CREATE OR REPLACE VIEW v_quality_trend AS
SELECT q.location_key, l.organisatie_naam, l.locatie_naam, l.plaats, q.procedure_id, q.verslagjaar,
       q.quality_verdict, q.n_beter, q.n_slechter, q.n_gemiddeld, q.volume
FROM quality_location q LEFT JOIN locations l USING (location_key)
ORDER BY q.procedure_id, l.organisatie_naam, q.verslagjaar;

CREATE OR REPLACE VIEW v_integrity AS
SELECT 'measurement without location' AS problem, count(*) AS n FROM measurements m
  WHERE NOT EXISTS (SELECT 1 FROM locations l WHERE l.location_key = m.location_key)
UNION ALL
SELECT 'measurement without indicator', count(*) FROM measurements m
  WHERE NOT EXISTS (SELECT 1 FROM indicators i WHERE i.indicator_code = m.indicator_code)
UNION ALL
SELECT 'location without coordinates', count(*) FROM locations WHERE lat IS NULL
UNION ALL
SELECT 'duplicate location_key', count(*) - count(DISTINCT location_key) FROM locations
UNION ALL
SELECT 'manual hospital AGB not in Zorginzicht', count(*) FROM hospitals_manual h
  WHERE h.agb_code IS NOT NULL AND NOT EXISTS (SELECT 1 FROM locations l WHERE l.organisatie_agb = h.agb_code);
"""


def build(path: Path = DB_PATH) -> Path:
    frames = load_frames()
    frames["quality_indicator"], frames["quality_location"] = quality_tables(frames["measurements"], frames["indicators"])
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp.duckdb")
    tmp.unlink(missing_ok=True)
    con = duckdb.connect(str(tmp))
    empty_schemas = {
        "locations": "location_key VARCHAR, organisatie_agb VARCHAR, organisatie_naam VARCHAR, locatie_naam VARCHAR, "
                     "postcode VARCHAR, plaats VARCHAR, lat DOUBLE, lon DOUBLE",
        "measurements": "procedure_id VARCHAR, verslagjaar INTEGER, location_key VARCHAR, indicator_code VARCHAR, "
                        "value VARCHAR, numerator DOUBLE, denominator DOUBLE",
        "indicators": "indicator_code VARCHAR, procedure_id VARCHAR, thema VARCHAR, indicator_naam VARCHAR, "
                      "eenheid VARCHAR, indicator_type VARCHAR, direction VARCHAR, label_nl VARCHAR",
        "quality_location": "location_key VARCHAR, procedure_id VARCHAR, quality_verdict VARCHAR, n_beter INTEGER, "
                            "n_slechter INTEGER, n_gemiddeld INTEGER, verslagjaar INTEGER, volume DOUBLE",
        "hospitals_manual": "location_id VARCHAR, agb_code VARCHAR",
        "quality_indicator": "location_key VARCHAR, procedure_id VARCHAR, indicator_code VARCHAR, verslagjaar INTEGER, "
                             "direction VARCHAR, indicator_nl VARCHAR, value VARCHAR, numerator DOUBLE, denominator DOUBLE, "
                             "n_waarnemingen DOUBLE, rate DOUBLE, ci_low DOUBLE, ci_high DOUBLE, national_rate DOUBLE, "
                             "method VARCHAR, verdict VARCHAR, position VARCHAR, source VARCHAR",
        "contracts": "year VARCHAR, location_id VARCHAR, concern VARCHAR, label VARCHAR, status VARCHAR, "
                     "omzetplafond VARCHAR, peildatum VARCHAR, source VARCHAR, source_url VARCHAR",
        "contract_candidates": "year VARCHAR, location_id VARCHAR, concern VARCHAR, label VARCHAR, status VARCHAR",
        "waiting_times": "procedure_id VARCHAR, location_key VARCHAR, weeks DOUBLE, wait_type VARCHAR, peildatum VARCHAR",
        "labels": "concern VARCHAR, label VARCHAR",
    }
    for name, df in frames.items():
        if df.empty and name in empty_schemas:
            con.execute(f"CREATE TABLE {name} ({empty_schemas[name]})")
        elif not df.empty:
            con.register("df", df)
            con.execute(f"CREATE TABLE {name} AS SELECT * FROM df")
            con.unregister("df")
        else:
            raise ValueError(f"no schema for empty table {name}")
    con.execute(VIEWS)
    con.close()
    tmp.replace(path)  # atomic: the app never sees a half-built database
    return path


def connect(read_only: bool = True) -> duckdb.DuckDBPyConnection:
    """Open the database, building it first when missing or older than its inputs."""
    inputs = [p for p in [REFERENCE / "locations.csv", REFERENCE / "indicators.csv", PROCESSED / "measurements.csv",
                          MANUAL / "contracts.csv", MANUAL / "indicators.csv", MANUAL / "hospitals.csv"] if p.exists()]
    if not DB_PATH.exists() or any(p.stat().st_mtime > DB_PATH.stat().st_mtime for p in inputs):
        build()
    return duckdb.connect(str(DB_PATH), read_only=read_only)


def main() -> int:
    path = build()
    con = duckdb.connect(str(path), read_only=True)
    for name, n in con.execute("SELECT table_name, estimated_size FROM duckdb_tables() ORDER BY 1").fetchall():
        print(f"{name:22s} {n:>9,}")
    problems = con.execute("SELECT * FROM v_integrity WHERE n > 0").fetchall()
    for problem, n in problems:
        print(f"INTEGRITY: {problem}: {n:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
