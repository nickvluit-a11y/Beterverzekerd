"""Compare each hospital's quality indicators with the national rate, honestly.

Method (per procedure × indicator × verslagjaar):
  * national rate = sum(numerator) / sum(denominator) over ALL providers in the source file
  * hospital rate with a 95% Wilson interval (works for small numbers and 0%)
  * 'beter' / 'slechter' only when the whole interval lies on one side of the national rate;
    otherwise 'gemiddeld'. Small hospitals therefore mostly land on 'gemiddeld' — on purpose:
    we do not claim a difference the data cannot show.
  * the direction (lower or higher is better) comes from data/manual/indicators.csv;
    indicators without a known direction are shown as numbers only, never judged.

Per hospital and procedure the verdicts are summarised (see hospital_verdict).
"""

from __future__ import annotations

import math
import re
from functools import lru_cache

import pandas as pd

from pipeline.reference import MANUAL

Z = 1.96  # 95%
VERDICTS = ["boven_gemiddeld", "gemiddeld", "gemengd", "onder_gemiddeld", "geen_data"]


@lru_cache
def indicator_meta() -> pd.DataFrame:
    return pd.read_csv(MANUAL / "indicators.csv")


def direction_for(procedure_id: str, indicator: object) -> tuple[str | None, str | None]:
    """(direction, Dutch label) for an indicator name, or (None, None) when unknown or ambiguous."""
    if not isinstance(indicator, str):
        return None, None
    rules = indicator_meta()
    rules = rules[rules["procedure_id"] == procedure_id]
    hits = [(r.direction, r.label_nl) for r in rules.itertuples()
            if re.search(r.indicator_pattern, indicator, flags=re.IGNORECASE)]
    directions = {d for d, _ in hits}
    return hits[0] if len(directions) == 1 else (None, None)


def wilson(numerator: float, denominator: float, z: float = Z) -> tuple[float, float]:
    if denominator <= 0:
        return math.nan, math.nan
    p = numerator / denominator
    centre = (p + z * z / (2 * denominator)) / (1 + z * z / denominator)
    half = z * math.sqrt(p * (1 - p) / denominator + z * z / (4 * denominator * denominator)) / (1 + z * z / denominator)
    return max(0.0, centre - half), min(1.0, centre + half)


def with_catalogue(measurements: pd.DataFrame, catalogue: pd.DataFrame) -> pd.DataFrame:
    """Measurements plus indicator name/theme/unit/type, and an `indicator` text used for direction rules."""
    cols = [c for c in ["indicator_code", "indicator_naam", "thema", "eenheid", "indicator_type"] if c in catalogue]
    df = measurements.merge(catalogue[cols].drop_duplicates("indicator_code"), on="indicator_code", how="left")
    df["indicator"] = (df.get("thema", "").fillna("").astype(str) + " | " + df.get("indicator_naam", "").fillna("").astype(str))
    return df


def compare(quality: pd.DataFrame) -> pd.DataFrame:
    """One row per location × indicator with rate, interval, national rate and verdict.

    Expects columns procedure_id, location_key, indicator (text), verslagjaar, numerator,
    denominator, value. The national rate uses every provider in the file, linked or not."""
    if quality.empty:
        return pd.DataFrame()
    df = quality.copy()
    df["num"] = pd.to_numeric(df.get("numerator"), errors="coerce")
    df["den"] = pd.to_numeric(df.get("denominator"), errors="coerce")
    meta = [direction_for(p, i) for p, i in zip(df["procedure_id"], df["indicator"])]
    df["direction"] = [m[0] for m in meta]
    df["indicator_nl"] = [m[1] for m in meta]

    ratio = df["den"].gt(0) & df["num"].ge(0) & (df["num"] <= df["den"])
    keys = ["procedure_id", "indicator_code" if "indicator_code" in df else "indicator", "verslagjaar"]
    totals = df[ratio].groupby(keys, dropna=False)[["num", "den"]].sum()
    national = (totals["num"] / totals["den"]).rename("national_rate")
    df = df.join(national, on=keys)

    rates, lows, highs, verdicts = [], [], [], []
    for row in df.itertuples():
        if not (row.den and row.den > 0 and 0 <= row.num <= row.den):
            rates.append(math.nan), lows.append(math.nan), highs.append(math.nan)
            verdicts.append("volume" if row.direction == "volume" else None)
            continue
        low, high = wilson(row.num, row.den)
        rates.append(row.num / row.den), lows.append(low), highs.append(high)
        if row.direction not in ("lower_better", "higher_better") or pd.isna(row.national_rate):
            verdicts.append(None)
        elif high < row.national_rate:
            verdicts.append("beter" if row.direction == "lower_better" else "slechter")
        elif low > row.national_rate:
            verdicts.append("slechter" if row.direction == "lower_better" else "beter")
        else:
            verdicts.append("gemiddeld")
    df["rate"], df["ci_low"], df["ci_high"], df["verdict"] = rates, lows, highs, verdicts
    return df.drop(columns=["num", "den"])


def hospital_verdict(compared: pd.DataFrame, procedure_id: str) -> pd.DataFrame:
    """Per location for one procedure (latest verslagjaar): counts of better/worse/average
    indicators and one summary verdict.

    boven_gemiddeld: at least one 'beter', no 'slechter'
    onder_gemiddeld: at least one 'slechter', no 'beter'
    gemengd:         both
    gemiddeld:       only 'gemiddeld'
    geen_data:       no judged indicators
    """
    columns = ["location_key", "quality_verdict", "n_beter", "n_slechter", "n_gemiddeld", "verslagjaar", "volume"]
    if compared.empty:
        return pd.DataFrame(columns=columns)
    sub = compared[(compared["procedure_id"] == procedure_id) & compared["location_key"].notna()].copy()
    if sub.empty:
        return pd.DataFrame(columns=columns)
    sub["year"] = pd.to_numeric(sub["verslagjaar"], errors="coerce")
    sub = sub[sub["year"] == sub.groupby("location_key")["year"].transform("max")]
    rows = []
    for location_key, group in sub.groupby("location_key"):
        counts = group["verdict"].value_counts()
        beter, slechter, gemiddeld = (int(counts.get(k, 0)) for k in ("beter", "slechter", "gemiddeld"))
        if beter and slechter:
            verdict = "gemengd"
        elif beter:
            verdict = "boven_gemiddeld"
        elif slechter:
            verdict = "onder_gemiddeld"
        elif gemiddeld:
            verdict = "gemiddeld"
        else:
            verdict = "geen_data"
        volume_rows = group[group["direction"] == "volume"]
        volume = pd.to_numeric(volume_rows["value"], errors="coerce").max() if not volume_rows.empty else math.nan
        rows.append({"location_key": location_key, "quality_verdict": verdict, "n_beter": beter,
                     "n_slechter": slechter, "n_gemiddeld": gemiddeld,
                     "verslagjaar": int(group["year"].max()) if group["year"].notna().any() else None,
                     "volume": volume})
    return pd.DataFrame(rows, columns=columns)
