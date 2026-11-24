"""Ingest the Zorginzicht MSZ open data (openbaar databestand, one Excel per verslagjaar).

The files share one schema (checked for verslagjaar 2022-2025; column names vary slightly in
spelling, which `canonical()` absorbs). Output is split into linked tables:

  data/reference/locations_zorginzicht.csv  every MSZ location in the files (all indicator sets),
                                            key = location_key (organisation AGB + postcode)
  data/reference/indicators.csv             catalogue: indicator code -> set, theme, name, unit, type
  data/processed/measurements.csv           our procedures only: location × indicator × verslagjaar
  docs/data_inventory/indicatoren.md        human-readable catalogue for our procedures

'Naleveringen' (late or corrected submissions) override the main file for the same
location × indicator × verslagjaar.

Usage: python -m pipeline.zorginzicht_ingest [raw_dir]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

from pipeline.reference import ROOT, procedures, save_with_history
from pipeline.tabular import read_any

REFERENCE = ROOT / "data" / "reference"
CATALOGUE_DOC = ROOT / "docs" / "data_inventory" / "indicatoren.md"

# canonical name -> normalised source spellings (lowercase, letters/digits only)
COLUMNS = {
    "verslagjaar": ["verslagjaar"],
    "organisatie_naam": ["organisatienaam"],
    "kvk": ["kvknummer"],
    "organisatie_agb": ["organisatieagbcode"],
    "locatie_naam": ["locatienaam"],
    "vestigingsnummer": ["vestigingsnummer"],
    "postcode": ["locatiepostcode"],
    "plaats": ["locatieplaats"],
    "huisnummer": ["locatiehuisnummer"],
    "locatie_agb": ["locatieagbcode"],
    "type_zorgaanbieder": ["typezorgaanbieder"],
    "indicatorset_code": ["indicatorsetcode"],
    "indicatorset_naam": ["indicatorsetnaam"],
    "thema": ["thema"],
    "indicator_code": ["indicatorcode"],
    "indicator_nummer": ["indicatornummer"],
    "indicator_naam": ["indicatornaam"],
    "eenheid": ["indicatoreenheid"],
    "indicator_type": ["indicatortype"],
    "value": ["indicatorwaarde"],
    "numerator": ["teller"],
    "denominator": ["noemer"],
    "n_waarnemingen": ["aantalwaarnemingen", "aantalwaarnemingenn"],
    "nvt": ["indicatornvt"],
    "meetperiode_eind": ["meetperiodeeinddatum"],
}
REQUIRED = {"organisatie_agb", "indicatorset_naam", "indicator_code", "value", "verslagjaar"}
LOCATION_FIELDS = ["location_key", "organisatie_agb", "organisatie_naam", "kvk", "locatie_agb", "locatie_naam",
                   "vestigingsnummer", "postcode", "huisnummer", "plaats", "type_zorgaanbieder"]
INDICATOR_FIELDS = ["indicator_code", "indicatorset_code", "indicatorset_naam", "indicator_nummer", "thema",
                    "indicator_naam", "eenheid", "indicator_type"]
MEASUREMENT_FIELDS = ["procedure_id", "verslagjaar", "location_key", "indicator_code", "value", "numerator",
                      "denominator", "n_waarnemingen", "nvt", "source"]


def _norm(name: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def canonical(df: pd.DataFrame) -> pd.DataFrame | None:
    """Rename source columns to canonical names; None if this is not a data sheet."""
    lookup = {_norm(c): c for c in df.columns}
    rename = {}
    for canon, spellings in COLUMNS.items():
        for spelling in spellings:
            if spelling in lookup:
                rename[lookup[spelling]] = canon
                break
    if not REQUIRED <= set(rename.values()):
        return None
    out = df.rename(columns=rename)[list(rename.values())].copy()
    for col in COLUMNS:
        if col not in out:
            out[col] = None
    return out


def agb(value: object) -> str | None:
    """AGB codes lose their leading zero in Excel: '6010901' -> '06010901'."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    digits = re.sub(r"\D", "", str(value).split(".")[0])
    return digits.zfill(8) if digits else None


def postcode(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    pc = re.sub(r"\s", "", value).upper()
    return pc if re.fullmatch(r"\d{4}[A-Z]{2}", pc) else None


def prepare(df: pd.DataFrame, source: str) -> pd.DataFrame:
    df = df.copy()
    for col in ("organisatie_agb", "locatie_agb"):
        df[col] = df[col].map(agb)
    df["postcode"] = df["postcode"].map(postcode)
    df["kvk"] = df["kvk"].map(agb)  # KvK numbers are 8 digits too
    df["verslagjaar"] = pd.to_numeric(df["verslagjaar"], errors="coerce").astype("Int64")
    df["location_key"] = df["organisatie_agb"].fillna("?") + "-" + df["postcode"].fillna("")
    df["source"] = source
    return df


def assign_procedure(set_names: pd.Series) -> pd.Series:
    """procedure_id from the exact indicator-set name (patterns in procedures.csv are anchored)."""
    result = pd.Series(pd.NA, index=set_names.index, dtype="object")
    text = set_names.fillna("").astype(str).str.strip()
    for proc in procedures().itertuples():
        result[text.str.contains(proc.zorginzicht_pattern, case=False, regex=True)] = proc.procedure_id
    return result


def latest_raw_dir() -> Path | None:
    base = ROOT / "data" / "raw" / "zorginzicht"
    dirs = sorted(p for p in base.glob("*") if p.is_dir()) if base.exists() else []
    return dirs[-1] if dirs else None


def load(source_dir: Path) -> pd.DataFrame:
    frames = []
    for path in sorted(source_dir.iterdir()):
        if path.suffix.lower() not in {".xlsx", ".xls", ".csv", ".zip"}:
            continue
        kind = "nalevering" if "nalever" in path.name.lower() else "odb"
        for sheet, df in read_any(path).items():
            data = canonical(df)
            if data is not None and not data.empty:
                frames.append(prepare(data, f"zorginzicht_{kind}:{path.name}:{sheet}"))
                print(f"read {path.name}:{sheet}: {len(data):,} rows")
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def build(all_rows: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """(locations, indicator catalogue, measurements for our procedures)."""
    locations = (all_rows.sort_values("verslagjaar")
                 .groupby("location_key", dropna=False).agg(
                     {**{f: "last" for f in LOCATION_FIELDS if f != "location_key"},
                      "verslagjaar": ["min", "max"]}))
    locations.columns = [c if isinstance(c, str) else (c[0] if c[1] == "last" else f"{c[0]}_{c[1]}")
                         for c in locations.columns]
    locations = locations.rename(columns={"verslagjaar_min": "first_year", "verslagjaar_max": "last_year"}).reset_index()

    ours = all_rows.assign(procedure_id=assign_procedure(all_rows["indicatorset_naam"]))
    ours = ours[ours["procedure_id"].notna()]
    catalogue = (ours.sort_values("verslagjaar").groupby("indicator_code")
                 .agg({**{f: "last" for f in INDICATOR_FIELDS if f != "indicator_code"},
                       "procedure_id": "last", "verslagjaar": lambda s: ",".join(str(y) for y in sorted(s.dropna().unique())),
                       "denominator": lambda s: int(pd.to_numeric(s, errors="coerce").gt(0).sum())})
                 .rename(columns={"verslagjaar": "years", "denominator": "rows_with_denominator"})
                 .reset_index())

    # a 'nalevering' replaces the main-file value for the same location × indicator × year
    ours = ours.assign(_prio=ours["source"].str.startswith("zorginzicht_nalevering").astype(int))
    ours = (ours.sort_values("_prio")
            .drop_duplicates(["verslagjaar", "location_key", "indicator_code"], keep="last"))
    measurements = ours[MEASUREMENT_FIELDS].sort_values(["procedure_id", "verslagjaar", "location_key", "indicator_code"])
    return locations, catalogue, measurements.reset_index(drop=True)


def catalogue_markdown(catalogue: pd.DataFrame) -> str:
    lines = ["# Indicatoren voor onze ingrepen (Zorginzicht)", "",
             "Automatisch gemaakt door `pipeline/zorginzicht_ingest.py`. `ratio` = aantal rijen met een noemer "
             "(alleen die indicatoren kunnen we statistisch vergelijken).", ""]
    for proc, group in catalogue.groupby("procedure_id"):
        lines += [f"## {proc}", "", "| code | nr | type | eenheid | thema | indicator | jaren | ratio |", "|---|---|---|---|---|---|---|---|"]
        for r in group.sort_values(["indicator_type", "indicator_nummer"]).itertuples():
            name = re.sub(r"\s+", " ", str(r.indicator_naam).replace("_x000D_", " "))[:160]
            lines.append(f"| {r.indicator_code} | {r.indicator_nummer} | {r.indicator_type} | {r.eenheid} | {r.thema} | "
                         f"{name.replace('|', '/')} | {r.years} | {r.rows_with_denominator} |")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    source_dir = Path(argv[0]) if argv else latest_raw_dir()
    if not source_dir:
        print("No raw Zorginzicht data; run scrapers.zorginzicht first.", file=sys.stderr)
        return 1
    rows = load(source_dir)
    if rows.empty:
        print("No sheets with the open-data schema found.", file=sys.stderr)
        return 1
    locations, catalogue, measurements = build(rows)
    REFERENCE.mkdir(parents=True, exist_ok=True)
    locations.to_csv(REFERENCE / "locations_zorginzicht.csv", index=False)
    catalogue.to_csv(REFERENCE / "indicators.csv", index=False)
    CATALOGUE_DOC.parent.mkdir(parents=True, exist_ok=True)
    CATALOGUE_DOC.write_text(catalogue_markdown(catalogue), encoding="utf-8")
    save_with_history(measurements, "measurements", source_dir.name)
    print(f"locations: {len(locations):,}; indicators for our procedures: {len(catalogue)}; "
          f"measurements: {len(measurements):,} ({measurements['verslagjaar'].min()}-{measurements['verslagjaar'].max()})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
