"""Measure how well the sources are linked, so linkage quality is monitored on every run.

Keys: location_key (organisation AGB + postcode) for locations, quality and waiting times;
organisation AGB for contracts (hospitals contract as one organisation).

Usage: python -m pipeline.linkage_report
Output: docs/data_inventory/koppeling.md
"""

from __future__ import annotations

import sys

import pandas as pd

from pipeline.reference import MANUAL, PROCESSED, REFERENCE, ROOT, hospitals

REPORT = ROOT / "docs" / "data_inventory" / "koppeling.md"


def _read(path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str) if path.exists() else pd.DataFrame()


def pct(part: int, whole: int) -> str:
    return f"{part:,}/{whole:,} ({part / whole:.0%})" if whole else "0/0"


def build_report() -> str:
    locations = _read(REFERENCE / "locations.csv")
    if locations.empty:
        locations = _read(REFERENCE / "locations_zorginzicht.csv")
    measurements = _read(PROCESSED / "measurements.csv")
    waits = _read(PROCESSED / "waiting_times.csv")
    candidates = _read(PROCESSED / "contracts_candidates.csv")
    checked = _read(MANUAL / "contracts.csv")
    manual = hospitals()
    lines = ["# Koppeling tussen bronnen", "",
             "Automatisch gemaakt door `pipeline/linkage_report.py` bij elke run. Sleutels: `location_key` "
             "(AGB organisatie + postcode) voor locaties, kwaliteit en wachttijden; AGB organisatie voor contracten.", ""]

    lines += ["## Locaties (Zorginzicht)", ""]
    if locations.empty:
        lines += ["Nog geen data.", ""]
    else:
        orgs = locations["organisatie_agb"].nunique()
        geo = int(locations["lat"].notna().sum()) if "lat" in locations else 0
        lines += [f"- {len(locations):,} locaties van {orgs:,} organisaties",
                  f"- met coördinaten: {pct(geo, len(locations))}", ""]

    lines += ["## Kwaliteit (metingen)", ""]
    if measurements.empty:
        lines += ["Nog geen data.", ""]
    else:
        known = set(locations["location_key"]) if not locations.empty else set()
        linked = measurements["location_key"].isin(known).sum()
        lines += [f"- {len(measurements):,} metingen, gekoppeld aan een locatie: {pct(linked, len(measurements))}", ""]
        per = (measurements.groupby(["procedure_id", "verslagjaar"])["location_key"].nunique()
               .unstack(fill_value=0))
        lines += ["Aantal locaties met metingen per ingreep en verslagjaar:", "",
                  "| ingreep | " + " | ".join(map(str, per.columns)) + " |", "|---|" + "---|" * len(per.columns)]
        lines += [f"| {proc} | " + " | ".join(str(v) for v in row) + " |" for proc, row in per.iterrows()]
        lines.append("")

    lines += ["## Contracten", ""]
    manual_agb = set(manual["agb_code"].dropna())
    known_agb = set(locations["organisatie_agb"].dropna()) if not locations.empty else set()
    lines += [f"- ziekenhuizen in `hospitals.csv` met AGB die ook in Zorginzicht staat: "
              f"{pct(len(manual_agb & known_agb), len(manual_agb))}"]
    if known_agb - manual_agb:
        lines.append(f"- organisaties in Zorginzicht zonder contractbron in `hospitals.csv`: {len(known_agb - manual_agb):,}")
    lines += [f"- contractkandidaten (nog te controleren): {len(candidates):,}",
              f"- gecontroleerde contracten: {len(checked):,}", ""]

    lines += ["## Wachttijden (NZa)", ""]
    if waits.empty:
        lines += ["Nog geen data (zie docs/bronnen.md).", ""]
    else:
        linked = waits["location_key"].notna().sum() if "location_key" in waits else 0
        lines += [f"- {len(waits):,} rijen, gekoppeld: {pct(int(linked), len(waits))}", ""]
    lines += integrity_lines()
    return "\n".join(lines) + "\n"


def integrity_lines() -> list[str]:
    """Linkage checks from the DuckDB view v_integrity (built by pipeline.build_db)."""
    from pipeline.build_db import DB_PATH
    if not DB_PATH.exists():
        return []
    import duckdb
    con = duckdb.connect(str(DB_PATH), read_only=True)
    rows = con.execute("SELECT problem, n FROM v_integrity").fetchall()
    con.close()
    lines = ["## Integriteit (DuckDB)", "", "| controle | aantal |", "|---|---|"]
    lines += [f"| {problem} | {'✅ 0' if n == 0 else f'⚠️ {n:,}'} |" for problem, n in rows]
    return lines + [""]


def main() -> int:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(build_report(), encoding="utf-8")
    print(f"linkage report: {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
