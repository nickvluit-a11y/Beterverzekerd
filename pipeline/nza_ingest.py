"""Waiting times per hospital location from the NZa open dataset 'Wachttijden medisch-specialistische zorg'.

The NZa file (semicolon CSV, cp1252) has one row per location × waiting-time type × peildatum, with
the organisation AGB code and the location postcode, so it links exactly to the Zorginzicht
locations (location_key = AGB + postcode). Waiting times are in days. We keep, per procedure,
the treatment wait (e.g. 'Initiële totale heupvervanging') and the first outpatient visit
(e.g. 'Orthopedie - Heupklachten'), as named in data/manual/procedures.csv.

Sources, newest first: a scraped file in data/raw/nza_wachttijden/<date>/ (the NZa site currently
blocks our bot) or a file downloaded by hand into data/manual/nza/wachttijden_<YYYY-MM-DD>.csv.

Output: data/processed/waiting_times.csv (+ dated history), docs/data_inventory/nza_wachttijden.md
Usage: python -m pipeline.nza_ingest [csv_path]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

from pipeline.reference import ROOT, procedures, save_with_history
from pipeline.tabular import decode

INVENTORY = ROOT / "docs" / "data_inventory" / "nza_wachttijden.md"
MANUAL_NZA = ROOT / "data" / "manual" / "nza"
REQUIRED = ["PEILDATUM", "AGBCODE", "POSTCODE", "TYPE_WACHTTIJD", "OMS_WACHTTIJD", "WACHTTIJD"]


def latest_source() -> tuple[Path, str] | None:
    """Newest waiting-time CSV (scraped or uploaded by hand) as (path, label)."""
    candidates = []
    raw = ROOT / "data" / "raw" / "nza_wachttijden"
    for path in raw.glob("*/wachttijden.csv") if raw.exists() else []:
        candidates.append((path.parent.name, path))
    for path in MANUAL_NZA.glob("*.csv") if MANUAL_NZA.exists() else []:
        match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
        candidates.append((match.group(1) if match else path.stem, path))
    if not candidates:
        return None
    label, path = max(candidates)
    return path, label


def read_nza(path: Path) -> pd.DataFrame:
    text = decode(path.read_bytes())
    from io import StringIO
    df = pd.read_csv(StringIO(text), sep=";", dtype=str)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise KeyError(f"NZa file misses columns {missing}; columns are {list(df.columns)}")
    return df


def extract(df: pd.DataFrame, label: str) -> pd.DataFrame:
    parts = []
    for proc in procedures().itertuples():
        for kind, description in (("behandeling", proc.nza_treatment), ("polikliniek", proc.nza_outpatient)):
            sub = df[df["OMS_WACHTTIJD"] == description]
            if sub.empty:
                continue
            parts.append(pd.DataFrame({
                "procedure_id": proc.procedure_id,
                "wait_type": kind,
                "organisatie_agb": sub["AGBCODE"].str.zfill(8),
                "postcode": sub["POSTCODE"].str.replace(" ", "").str.upper(),
                "location_name": sub.get("NAAM_VESTIGING"),
                "plaats": sub.get("PLAATS"),
                "days": pd.to_numeric(sub["WACHTTIJD"], errors="coerce"),
                "peildatum": sub["PEILDATUM"],
                "insufficient": sub.get("INSUFFICIENT_OBSERVATIONS", pd.Series("FALSE", index=sub.index)).str.upper() == "TRUE",
            }))
    if not parts:
        return pd.DataFrame()
    out = pd.concat(parts, ignore_index=True)
    out["location_key"] = link_locations(out["organisatie_agb"], out["postcode"].fillna(""))
    out["weeks"] = (out["days"] / 7).round(1)
    out["source"] = "NZa open data wachttijden msz"
    out["fetched_on"] = label
    return out


def link_locations(agb: pd.Series, postcode: pd.Series) -> pd.Series:
    """Zorginzicht location_key for each NZa row: exact AGB + postcode; else the same AGB in the same
    PC4 area; else the organisation's only location. Unmatched rows keep their own AGB + postcode."""
    path = ROOT / "data" / "reference" / "locations_zorginzicht.csv"
    exact = agb + "-" + postcode
    if not path.exists():
        return exact
    locations = pd.read_csv(path, dtype=str)[["location_key", "organisatie_agb", "postcode"]].dropna(subset=["organisatie_agb"])
    known = set(locations["location_key"])
    by_pc4 = (locations.assign(pc4=locations["postcode"].str[:4]).drop_duplicates(["organisatie_agb", "pc4"], keep=False)
              .set_index(["organisatie_agb", "pc4"])["location_key"])
    single = locations.groupby("organisatie_agb")["location_key"].agg(lambda s: s.iloc[0] if len(s) == 1 else None).dropna()
    result = []
    for a, pc, key in zip(agb, postcode, exact):
        if key in known:
            result.append(key)
        elif (a, pc[:4]) in by_pc4.index:
            result.append(by_pc4[(a, pc[:4])])
        elif a in single.index:
            result.append(single[a])
        else:
            result.append(key)
    return pd.Series(result, index=agb.index)


def inventory(df: pd.DataFrame, waits: pd.DataFrame, label: str) -> str:
    latest = waits[waits["peildatum"] == waits["peildatum"].max()]
    lines = [f"# NZa wachttijden ({label})", "",
             f"{len(df):,} rijen in het bronbestand, {df['PEILDATUM'].nunique()} peildata "
             f"({df['PEILDATUM'].min()} t/m {df['PEILDATUM'].max()}).", "",
             f"Voor onze ingrepen: {len(waits):,} rijen; laatste peildatum {waits['peildatum'].max()}.", "",
             "| ingreep | soort | locaties | mediaan dagen | te weinig waarnemingen |", "|---|---|---|---|---|"]
    for (proc, kind), g in latest.groupby(["procedure_id", "wait_type"]):
        lines.append(f"| {proc} | {kind} | {g['location_key'].nunique()} | {g['days'].median():.0f} | {int(g['insufficient'].sum())} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    source = (Path(argv[0]), Path(argv[0]).stem) if argv else latest_source()
    if not source:
        print("No NZa data: the scraper is blocked and nothing is in data/manual/nza/.", file=sys.stderr)
        return 1
    path, label = source
    df = read_nza(path)
    waits = extract(df, label)
    if waits.empty:
        print("No rows for our procedures; check the descriptions in procedures.csv.", file=sys.stderr)
        return 1
    INVENTORY.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY.write_text(inventory(df, waits, label), encoding="utf-8")
    save_with_history(waits, "waiting_times", label)
    print(f"waiting_times.csv: {len(waits):,} rows from {path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
