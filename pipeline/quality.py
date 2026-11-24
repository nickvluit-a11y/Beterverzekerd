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


def direction_for(procedure_id: str, indicator: object, code: object = None) -> tuple[str | None, str | None]:
    """(direction, Dutch label) for an indicator, or (None, None) when unknown or ambiguous.

    A rule for the exact indicator code wins (direction 'none' = deliberately not judged);
    otherwise name patterns are tried."""
    rules = indicator_meta()
    if isinstance(code, str) and "indicator_code" in rules:
        exact = rules[rules["indicator_code"] == code]
        if not exact.empty:
            direction = exact.iloc[0]["direction"]
            return (None if direction == "none" else direction), exact.iloc[0]["label_nl"]
    if not isinstance(indicator, str):
        return None, None
    rules = rules[(rules["procedure_id"] == procedure_id) & rules["indicator_pattern"].notna()]
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
    cols = [c for c in ["indicator_code", "indicator_naam", "thema", "eenheid", "indicator_type", "indicator_nummer"]
            if c in catalogue]
    df = measurements.merge(catalogue[cols].drop_duplicates("indicator_code"), on="indicator_code", how="left")
    df["indicator"] = (df.get("thema", "").fillna("").astype(str) + " | " + df.get("indicator_naam", "").fillna("").astype(str))
    return df


# Zorginzicht publishes some indicators as a group of rows: a point estimate plus the official
# 95% interval (and N). The role is the last phrase of the indicator name.
_ROLE = re.compile(r"(aantal \(n\)|gemiddelde|gecorrigeerd percentage|"
                   r"95\s*% betrouwbaarheidsinterval (?:lower|upper) bound)\.?\s*$", re.IGNORECASE)


def _role_name(phrase: str) -> str:
    phrase = phrase.lower()
    if phrase.startswith("aantal"):
        return "n"
    if "lower" in phrase:
        return "lower"
    if "upper" in phrase:
        return "upper"
    return "point"
_SCALES = ["EQ-5D index", "EQ-5D thermometer", "OHS", "OKS", "NRS-pijn rust", "NRS-pijn activiteit", "CatQuest"]
MIN_UNITS_FOR_TAU = 10  # hospitals needed to estimate between-hospital variance
MIN_PROM_RESPONSE = 50.0  # % pre-operative PROM response below which PROM results are not judged


def interval_role(text: object) -> tuple[str | None, str | None]:
    """(stem, role) for an indicator text that is part of a published point/interval group."""
    if not isinstance(text, str):
        return None, None
    clean = re.sub(r"\s+", " ", text.replace("_x000D_", " ")).strip()
    match = _ROLE.search(clean)
    if not match:
        return None, None
    return clean[:match.start()].strip(" .|"), _role_name(match.group(1))


def interval_label(stem: str) -> str:
    scale = next((s for s in _SCALES if s.lower() in stem.lower()), None)
    if "revisie" in stem.lower():
        horizon = re.search(r"binnen (\w+) jaar", stem, re.IGNORECASE)
        return f"Revisie binnen {horizon.group(1) if horizon else '?'} jaar (gecorrigeerd)"
    if "preoperatieve" in stem.lower() or "preoperatievescore" in stem.lower():
        return f"Score vóór de operatie: {scale or 'PROM'}"
    months = re.search(r"(\d+) maanden", stem)
    return f"Verbetering volgens patiënt na {months.group(1) if months else '?'} mnd: {scale or 'PROM'}"


def interval_direction(stem: str, points: pd.Series) -> str | None:
    """Revision: lower is better. PROM difference at 12 months: the direction in which patients
    improve nationally (the sign of the median change). Pre-operative scores and earlier PROM
    follow-ups are shown but not judged (case-mix, incomplete recovery)."""
    low = stem.lower()
    if "revisie" in low:
        return "lower_better"
    if "verschilscore" in low and "12 maanden" in low:
        median = points.median()
        return None if pd.isna(median) or median == 0 else ("higher_better" if median > 0 else "lower_better")
    return None


def compare_intervals(df: pd.DataFrame) -> pd.DataFrame:
    """Judge published point estimates against the national median using the official 95% interval."""
    roles = df["indicator"].map(interval_role)
    df = df.assign(_name=[r[0] for r in roles], _role=[r[1] for r in roles])
    df = df[df["_role"].notna()].copy()
    if df.empty:
        return pd.DataFrame()
    # group the rows of one published indicator by its official number (4d1a/b/c/d -> 4d1, 5a1/2/3 -> 5a):
    # the source spells names inconsistently ('95 %', 'OHS-PS' vs 'OHS'); the name is the fallback
    if "indicator_nummer" in df:
        number = df["indicator_nummer"].astype(str).str.strip()
        df["_stem"] = (df.get("thema", "").fillna("").astype(str) + " #" + number.str[:-1]).where(
            df["indicator_nummer"].notna(), df["_name"])
    else:
        df["_stem"] = df["_name"]
    names = df[df["_role"] == "point"].groupby("_stem")["_name"].first()
    df["_v"] = pd.to_numeric(df["value"].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    keys = ["procedure_id", "location_key", "verslagjaar", "_stem"]
    wide = df.pivot_table(index=keys, columns="_role", values="_v", aggfunc="first")
    codes = df[df["_role"] == "point"].set_index(keys)["indicator_code"] if "indicator_code" in df else None
    wide = wide.reset_index()
    if not {"point", "lower", "upper"} <= set(wide.columns):
        return pd.DataFrame()
    wide = wide.dropna(subset=["point", "lower", "upper"])
    # a point outside its own interval is a data error in the source: not judged
    wide["consistent"] = (wide["lower"] <= wide["point"]) & (wide["point"] <= wide["upper"])
    rows = []
    for (proc, stem, year), group in wide.groupby(["procedure_id", "_stem", "verslagjaar"], dropna=False):
        national = group.loc[group["consistent"], "point"].median()
        direction = interval_direction(names.get(stem, stem), group.loc[group["consistent"], "point"])
        se = ((group["upper"] - group["lower"]) / (2 * Z)).where(group["consistent"])
        verdicts = funnel_verdicts(group["point"], se, national, direction)
        for r in group.itertuples():
            verdict = verdicts.get(r.Index)
            verdict = None if (verdict is None or pd.isna(verdict)) else verdict
            code = codes.get((proc, r.location_key, year, stem)) if codes is not None else None
            if isinstance(code, pd.Series):
                code = code.iloc[0]
            rows.append({"procedure_id": proc, "location_key": r.location_key, "verslagjaar": year,
                         "indicator_code": code, "indicator": names.get(stem, stem),
                         "indicator_nl": interval_label(names.get(stem, stem)), "direction": direction, "value": r.point, "rate": r.point, "ci_low": r.lower,
                         "ci_high": r.upper, "national_rate": national, "n_waarnemingen": getattr(r, "n", None),
                         "verdict": verdict, "method": "interval",
                         "position": None if r.consistent else "inconsistent in bron"})
    return pd.DataFrame(rows)


def apply_prom_response_filter(df: pd.DataFrame) -> pd.DataFrame:
    """PROM verdicts only count when the pre-operative PROM response is at least MIN_PROM_RESPONSE %."""
    if df.empty or "indicator" not in df:
        return df
    response = df[df["indicator"].astype(str).str.contains("Responspercentage pre-operatief", case=False, na=False)]
    if response.empty:
        return df
    rate = pd.to_numeric(response["value"].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    keys = zip(response["procedure_id"], response["location_key"], response["verslagjaar"])
    low = {k for k, v in zip(keys, rate) if pd.notna(v) and v < MIN_PROM_RESPONSE}
    is_prom = df["indicator_nl"].astype(str).str.startswith("Verbetering volgens patiënt")
    in_low = pd.Series([k in low for k in zip(df["procedure_id"], df["location_key"], df["verslagjaar"])], index=df.index)
    hit = is_prom & in_low
    df.loc[hit, "verdict"] = None
    df.loc[hit, "position"] = f"PROM-respons < {MIN_PROM_RESPONSE:.0f}%: niet beoordeeld"
    return df


def funnel_verdicts(y: pd.Series, se: pd.Series, reference: float, direction: str | None,
                    winsor: float = 0.1) -> pd.Series:
    """'beter' / 'slechter' / 'gemiddeld' with overdispersion correction (Spiegelhalter 2005).

    Hospitals always differ somewhat beyond chance (registration, case mix). That between-hospital
    variance tau² is estimated from winsorised z-scores (DerSimonian-Laird style) and added to each
    hospital's own sampling variance, so a verdict needs a difference larger than the usual spread.
    """
    out = pd.Series(None, index=y.index, dtype="object")
    ok = y.notna() & se.notna() & (se > 0)
    if direction not in ("lower_better", "higher_better") or pd.isna(reference) or ok.sum() == 0:
        return out
    y, se = y[ok].astype(float), se[ok].astype(float)
    z = (y - reference) / se
    if len(z) >= 10:
        low, high = z.quantile(winsor), z.quantile(1 - winsor)
        z_w = z.clip(low, high)
    else:
        z_w = z
    n = len(z_w)
    phi = float((z_w ** 2).mean())
    w = 1 / se ** 2
    # the spread between hospitals can only be estimated with enough hospitals
    tau2 = max(0.0, (n * phi - (n - 1)) / (w.sum() - (w ** 2).sum() / w.sum())) if n >= MIN_UNITS_FOR_TAU else 0.0
    limit = Z * (se ** 2 + tau2) ** 0.5
    above, below = y > reference + limit, y < reference - limit
    higher_is_better = direction == "higher_better"
    out[ok] = "gemiddeld"
    out[above[above].index] = "beter" if higher_is_better else "slechter"
    out[below[below].index] = "slechter" if higher_is_better else "beter"
    return out


def compare(quality: pd.DataFrame) -> pd.DataFrame:
    """One row per location × indicator with rate, interval, national rate and verdict.

    Expects columns procedure_id, location_key, indicator (text), verslagjaar, numerator,
    denominator, value. The national rate uses every provider in the file, linked or not."""
    if quality.empty:
        return pd.DataFrame()
    df = quality.copy()
    df["num"] = pd.to_numeric(df.get("numerator"), errors="coerce")
    df["den"] = pd.to_numeric(df.get("denominator"), errors="coerce")
    codes = df["indicator_code"] if "indicator_code" in df else pd.Series([None] * len(df), index=df.index)
    cache: dict[tuple, tuple] = {}

    def lookup(key: tuple) -> tuple:
        if key not in cache:  # one rule lookup per distinct indicator, not per row
            proc, text, code = key
            cache[key] = (None, None) if interval_role(text)[1] else direction_for(proc, text, code)
        return cache[key]
    meta = [lookup(k) for k in zip(df["procedure_id"], df["indicator"], codes)]
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
        verdicts.append(None)  # set per indicator × year below (funnel with overdispersion)
    df["rate"], df["ci_low"], df["ci_high"], df["verdict"] = rates, lows, highs, verdicts
    judged = df["rate"].notna() & df["direction"].isin(["lower_better", "higher_better"])
    for _, group in df[judged].groupby(keys, dropna=False):
        p0 = group["national_rate"].iloc[0]
        se = (p0 * (1 - p0) / group["den"]) ** 0.5 if 0 < p0 < 1 else pd.Series(float("nan"), index=group.index)
        df.loc[group.index, "verdict"] = funnel_verdicts(group["rate"], se, p0, group["direction"].iloc[0])
    df["method"] = ["ratio" if not pd.isna(r) else None for r in rates]
    df = _mean_scores(df, keys)
    intervals = compare_intervals(df)
    df = df.drop(columns=["num", "den"])
    if not intervals.empty:
        df = pd.concat([df, intervals], ignore_index=True)
    return apply_prom_response_filter(df)


def _mean_scores(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Scores without numerator/denominator (e.g. PROM 'verschilscore', a mean change per patient).

    Without a spread per hospital no confidence interval is possible, so these are NOT judged.
    They are shown next to the national mean (weighted by the number of patients) with a neutral
    'position': gunstiger / ongunstiger than the national mean, given the indicator's direction."""
    value = pd.to_numeric(df.get("value").astype(str).str.replace(",", ".", regex=False), errors="coerce") \
        if "value" in df else pd.Series(math.nan, index=df.index)
    is_mean = df["method"].isna() & value.notna() & df["direction"].isin(["lower_better", "higher_better"])
    if "eenheid" in df:  # a percentage without numerator/denominator is not a mean score
        is_mean &= df["eenheid"].astype(str).str.lower().isin(["gemiddelde", "getal", "score", "nan", "none"])
    df["position"] = None
    if not is_mean.any():
        return df
    weight = pd.to_numeric(df.get("n_waarnemingen"), errors="coerce").fillna(1.0) if "n_waarnemingen" in df \
        else pd.Series(1.0, index=df.index)
    sub = df[is_mean].assign(_v=value[is_mean], _w=weight[is_mean])
    national = (sub.assign(_vw=sub["_v"] * sub["_w"]).groupby(keys, dropna=False)[["_vw", "_w"]].sum())
    national = (national["_vw"] / national["_w"]).rename("_national_mean")
    sub = sub.join(national, on=keys)
    better_if_higher = sub["direction"] == "higher_better"
    favourable = (sub["_v"] > sub["_national_mean"]) == better_if_higher
    df.loc[is_mean, "rate"] = sub["_v"]
    df.loc[is_mean, "national_rate"] = sub["_national_mean"]
    df.loc[is_mean, "method"] = "mean"
    df.loc[is_mean, "position"] = favourable.map({True: "gunstiger", False: "ongunstiger"}).where(sub["_v"] != sub["_national_mean"], "gelijk")
    return df


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


# Plain-language domains for the app. Correlated indicators (five PROM scales from the same
# patients) collapse into one domain, so one strong area does not count five times.
DOMAINS = [
    ("heroperatie", r"revisie", "Minder heroperaties", "Meer heroperaties"),
    ("infectie", r"wondinfectie", "Minder infecties", "Meer infecties"),
    ("herstel", r"verbetering volgens patiënt", "Patiënten melden meer herstel", "Patiënten melden minder herstel"),
    ("zien", r"beter zien", "Vaker beter zicht na de operatie", "Minder vaak beter zicht"),
    ("sterkte", r"refractie", "Vaker de beoogde sterkte", "Minder vaak de beoogde sterkte"),
]


def domain_of(indicator_nl: object) -> str | None:
    text = str(indicator_nl).lower()
    return next((d for d, pattern, _, _ in DOMAINS if re.search(pattern, text)), None)


def domain_highlights(rows: pd.DataFrame) -> list[tuple[str, str]]:
    """[(verdict, sentence)] per domain for one location: a domain is 'beter' when at least one of its
    indicators is better and none worse, 'slechter' in the reverse case; mixed domains are left out."""
    out = []
    for domain, _, better_text, worse_text in DOMAINS:
        verdicts = set(rows.loc[rows["indicator_nl"].map(domain_of) == domain, "verdict"].dropna())
        if "beter" in verdicts and "slechter" not in verdicts:
            out.append(("beter", better_text))
        elif "slechter" in verdicts and "beter" not in verdicts:
            out.append(("slechter", worse_text))
    return out
