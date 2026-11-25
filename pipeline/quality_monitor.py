"""Quality monitor: how hospital quality develops over the years, straight from the DuckDB database.

    python -m pipeline.quality_monitor   -> docs/kwaliteitsmonitor.md

Per procedure:
  * national value per judged indicator per verslagjaar (is Dutch care getting better?)
  * number of hospitals above / around / below average per year
  * hospitals that are consistently above or below average (at least 2 of the last 3 years)
  * hospitals whose verdict improved or declined between the last two years
All verdicts use the method in pipeline/quality.py (official intervals, overdispersion correction).
"""

from __future__ import annotations

import sys

import duckdb
import pandas as pd

from pipeline.build_db import connect
from pipeline.reference import ROOT

REPORT = ROOT / "docs" / "kwaliteitsmonitor.md"
PROCEDURE_NAMES = {"heup": "Heupprothese", "knie": "Knieprothese", "staar": "Staaroperatie (cataract)"}
RANK = {"onder_gemiddeld": 0, "gemengd": 1, "gemiddeld": 1, "boven_gemiddeld": 2}


def _table(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["_geen_", ""]
    cols = list(df.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for row in df.itertuples(index=False):
        cells = []
        for v in row:
            if pd.isna(v):
                cells.append("")
            elif isinstance(v, float):
                cells.append(f"{v:.0f}" if v.is_integer() and abs(v) >= 10 or v == 0 else f"{v:.2f}")
            else:
                cells.append(str(v).replace("|", "/"))
        lines.append("| " + " | ".join(cells) + " |")
    return lines + [""]


def national_trend(con: duckdb.DuckDBPyConnection, procedure_id: str) -> pd.DataFrame:
    df = con.execute("""
        SELECT indicator_nl AS indicator, method, verslagjaar, any_value(national_rate) AS landelijk
        FROM quality_indicator
        WHERE procedure_id = ? AND verdict IN ('beter', 'slechter', 'gemiddeld')
        GROUP BY ALL
    """, [procedure_id]).df()
    if df.empty:
        return df
    df.loc[df["method"] == "ratio", "landelijk"] *= 100  # fractions -> percentages
    wide = df.pivot_table(index="indicator", columns="verslagjaar", values="landelijk").reset_index()
    wide.columns = [str(c) for c in wide.columns]
    return wide


def verdict_counts(con: duckdb.DuckDBPyConnection, procedure_id: str) -> pd.DataFrame:
    df = con.execute("""
        SELECT verslagjaar, quality_verdict, count(*) AS n FROM quality_location
        WHERE procedure_id = ? GROUP BY ALL
    """, [procedure_id]).df()
    if df.empty:
        return df
    wide = df.pivot_table(index="verslagjaar", columns="quality_verdict", values="n", fill_value=0).astype(int).reset_index()
    order = ["verslagjaar", "boven_gemiddeld", "gemiddeld", "gemengd", "onder_gemiddeld", "geen_data"]
    return wide[[c for c in order if c in wide.columns]]


def trajectories(con: duckdb.DuckDBPyConnection, procedure_id: str) -> pd.DataFrame:
    return con.execute("""
        SELECT location_key, coalesce(locatie_naam, organisatie_naam) || ' (' || coalesce(plaats, '') || ')' AS ziekenhuis,
               verslagjaar, quality_verdict
        FROM v_quality_trend WHERE procedure_id = ?
    """, [procedure_id]).df()


def consistent(traj: pd.DataFrame, verdict: str, years: list[int]) -> pd.DataFrame:
    recent = traj[traj["verslagjaar"].isin(years)]
    hits = recent[recent["quality_verdict"] == verdict].groupby("ziekenhuis")["verslagjaar"].apply(
        lambda s: ", ".join(str(int(y)) for y in sorted(s)))
    counts = recent[recent["quality_verdict"] == verdict].groupby("ziekenhuis").size()
    keep = counts[counts >= 2].index
    return pd.DataFrame({"ziekenhuis": keep, "jaren": [hits[k] for k in keep]}).sort_values("ziekenhuis")


def changes(traj: pd.DataFrame, last: int, previous: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    pivot = traj.pivot_table(index="ziekenhuis", columns="verslagjaar", values="quality_verdict", aggfunc="first")
    if last not in pivot or previous not in pivot:
        return pd.DataFrame(), pd.DataFrame()
    both = pivot[[previous, last]].dropna()
    both = both[both[previous].isin(RANK) & both[last].isin(RANK)]
    delta = both[last].map(RANK) - both[previous].map(RANK)
    fmt = lambda d: pd.DataFrame({"ziekenhuis": d.index, str(previous): d[previous].values, str(last): d[last].values})  # noqa: E731
    return fmt(both[delta > 0]), fmt(both[delta < 0])


def build_report(con: duckdb.DuckDBPyConnection) -> str:
    years = [int(y) for (y,) in con.execute("SELECT DISTINCT verslagjaar FROM quality_location ORDER BY 1").fetchall()]
    lines = ["# Kwaliteitsmonitor", "",
             "Automatisch gemaakt door `pipeline/quality_monitor.py` uit de openbare kwaliteitsdata van Zorginzicht. "
             "Een ziekenhuis is alleen 'boven' of 'onder' gemiddeld als het verschil groter is dan de gebruikelijke "
             "spreiding tussen ziekenhuizen (95%-interval met correctie voor overdispersie). Geen ranglijst: kleine "
             "aantallen en verschillen in patiëntengroepen maken die misleidend.", "",
             "**Let op patiëntenmix.** Alleen het revisiepercentage is gecorrigeerd voor patiëntkenmerken. "
             "Academische en topklinische centra behandelen vaker complexe patiënten en kunnen daardoor op "
             "ongecorrigeerde indicatoren (zoals PROM-verbetering en infecties) lager uitkomen zonder slechtere zorg. "
             "Zelfstandige klinieken behandelen juist vaker gezondere patiënten.", ""]
    if not years:
        return "\n".join(lines + ["Nog geen kwaliteitsdata.", ""])
    recent = years[-3:]
    for proc, name in PROCEDURE_NAMES.items():
        lines += [f"## {name}", "", "### Landelijk niveau per indicator", "",
                  "(percentages voor uitkomsten; gemiddelde verbetering in punten voor PROMs; mediaan van ziekenhuizen "
                  "voor gecorrigeerde en gepubliceerde scores)", ""]
        lines += _table(national_trend(con, proc))
        lines += ["### Aantal ziekenhuislocaties per oordeel", ""] + _table(verdict_counts(con, proc))
        traj = trajectories(con, proc)
        lines += [f"### Structureel boven gemiddeld (minstens 2 van {', '.join(map(str, recent))})", ""]
        lines += _table(consistent(traj, "boven_gemiddeld", recent))
        lines += [f"### Structureel onder gemiddeld (minstens 2 van {', '.join(map(str, recent))})", ""]
        lines += _table(consistent(traj, "onder_gemiddeld", recent))
        if len(years) >= 2:
            better, worse = changes(traj, years[-1], years[-2])
            lines += [f"### Verbeterd van {years[-2]} naar {years[-1]}", ""] + _table(better)
            lines += [f"### Verslechterd van {years[-2]} naar {years[-1]}", ""] + _table(worse)
    return "\n".join(lines)


def main() -> int:
    con = connect()
    REPORT.write_text(build_report(con), encoding="utf-8")
    print(f"quality monitor: {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
