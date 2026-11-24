"""Measure how well the sources are linked to each other, so linkage quality is monitored per run.

For every processed source: rows, share linked to a location in hospitals.csv, and the most
frequent provider names/AGB codes that did not link (the to-do list for hospitals.csv aliases).
Also: per location, which layers (quality, waiting times, contracts) are present.

Usage: python -m pipeline.linkage_report
Output: docs/data_inventory/koppeling.md
"""

from __future__ import annotations

import sys

import pandas as pd

from pipeline.reference import MANUAL, PROCESSED, ROOT, hospitals

REPORT = ROOT / "docs" / "data_inventory" / "koppeling.md"
SOURCES = {
    "Kwaliteit (Zorginzicht)": PROCESSED / "quality.csv",
    "Wachttijden (NZa)": PROCESSED / "waiting_times.csv",
    "Contracten, kandidaten": PROCESSED / "contracts_candidates.csv",
    "Contracten, gecontroleerd": MANUAL / "contracts.csv",
}


def source_section(name: str, df: pd.DataFrame) -> list[str]:
    lines = [f"## {name}", ""]
    if df.empty:
        return lines + ["Geen data.", ""]
    linked = df["location_id"].notna() if "location_id" in df else pd.Series(False, index=df.index)
    lines.append(f"{len(df):,} rijen, waarvan **{linked.mean():.0%} gekoppeld** aan een ziekenhuislocatie.")
    if "provider_raw" in df and (~linked).any():
        cols = [c for c in ["provider_raw", "agb_code", "city_raw"] if c in df]
        top = df[~linked].groupby(cols, dropna=False).size().sort_values(ascending=False).head(30)
        lines += ["", "Meest voorkomende niet-gekoppelde aanbieders:", "", "| " + " | ".join(cols) + " | rijen |",
                  "|" + "---|" * (len(cols) + 1)]
        for key, count in top.items():
            key = key if isinstance(key, tuple) else (key,)
            lines.append("| " + " | ".join("" if pd.isna(k) else str(k) for k in key) + f" | {count} |")
    return lines + [""]


def coverage_section(frames: dict[str, pd.DataFrame]) -> list[str]:
    table = hospitals()[["location_id", "location_name"]].copy()
    for name, df in frames.items():
        present = set(df["location_id"].dropna()) if "location_id" in df else set()
        table[name] = table["location_id"].map(lambda x, p=present: "✓" if x in p else "–")
    lines = ["## Dekking per ziekenhuislocatie", "", "| " + " | ".join(table.columns[1:]) + " |",
             "|" + "---|" * (len(table.columns) - 1)]
    lines += ["| " + " | ".join(str(v) for v in row[1:]) + " |" for row in table.itertuples(index=False)]
    return lines + [""]


def main() -> int:
    frames = {name: pd.read_csv(path) if path.exists() else pd.DataFrame() for name, path in SOURCES.items()}
    lines = ["# Koppeling tussen bronnen", "",
             "Automatisch gemaakt door `pipeline/linkage_report.py`. Doel: elke bron koppelen aan dezelfde "
             "ziekenhuislocatie, want pas dan is kwaliteit per polis te vergelijken.", ""]
    for name, df in frames.items():
        lines += source_section(name, df)
    lines += coverage_section(frames)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"linkage report: {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
