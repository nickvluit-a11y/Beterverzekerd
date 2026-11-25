"""Compare each hospital's quality indicators with the national level, honestly.

Three kinds of indicators (per procedure × indicator × verslagjaar):

1. Ratios (numerator/denominator, e.g. deep wound infection, vision gain after cataract surgery)
   * national rate = pooled sum(numerator) / sum(denominator) over all providers
   * compared on the arcsine-square-root scale (variance-stabilising; Spiegelhalter 2005), which
     behaves well for rare events and rates near 100%
   * not judged when fewer than MIN_RATIO_COVERAGE of the reporting hospitals publish a
     numerator/denominator (the national rate would be biased)
2. Published point + official 95% interval (case-mix corrected revision rates; PROM change scores)
   * source placeholders (0/0/0 or N = 0) are dropped, swapped bounds are repaired, implausible
     values and points outside their own interval are flagged as source errors, PROMs need N >= 20
   * reference: inverse-variance weighted mean for revision (benchmark = national rate),
     median of hospitals for PROMs
   * the half of the published interval facing the reference gives the standard error
   * PROMs only when the pre-operative PROM response is at least MIN_PROM_RESPONSE %
3. Everything else (volume, structure, registry completeness, pre-operative scores, means
   without spread) is shown but never judged.

Verdicts use a funnel with overdispersion correction: a hospital is only 'beter' / 'slechter'
when it differs by more than the usual between-hospital spread. Indicators are summarised per
domain (heroperaties, infecties, herstel volgens patiënt, zicht, sterkte), so the five
correlated PROM scales count once.
"""

from __future__ import annotations

import math
import re
from functools import lru_cache

import numpy as np
import pandas as pd

from pipeline.reference import MANUAL

Z = 1.96  # 95%: confidence intervals shown to users
# Asymmetric evidence thresholds (owner's choice): a positive signal needs less certainty than
# calling a named hospital worse, because a wrong 'slechter' does more harm.
Z_BETTER = 1.2816  # 80% two-sided
Z_WORSE = 1.96     # 95% two-sided
VERDICTS = ["boven_gemiddeld", "gemiddeld", "gemengd", "onder_gemiddeld", "geen_data"]
MIN_UNITS_FOR_TAU = 10      # hospitals needed to estimate the between-hospital variance
MIN_PROM_RESPONSE = 50.0    # % pre-operative PROM response needed to judge PROM results
MIN_N_PROM = 20             # patients needed to judge a PROM change score
MIN_RATIO_COVERAGE = 0.7    # share of hospitals that must publish numerator/denominator
PLAUSIBLE_CHANGE = {        # largest possible change per PROM scale
    "eq-5d index": 1.6, "eq-5d thermometer": 100, "nrs-pijn": 10, "ohs": 48, "oks": 48,
}
_SCALES = ["EQ-5D index", "EQ-5D thermometer", "OHS", "OKS", "NRS-pijn rust", "NRS-pijn activiteit", "CatQuest"]
_DISEASE_SPECIFIC = ("OHS", "OKS")


# --- rules ------------------------------------------------------------------------------------

@lru_cache
def indicator_meta() -> pd.DataFrame:
    return pd.read_csv(MANUAL / "indicators.csv")


def direction_for(procedure_id: str, indicator: object, code: object = None) -> tuple[str | None, str | None]:
    """(direction, Dutch label) for an indicator, or (None, None) when unknown or ambiguous.

    A rule for the exact indicator code wins (direction 'none' = deliberately not judged);
    otherwise name patterns are tried (only used in tests)."""
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
    return hits[0] if len({d for d, _ in hits}) == 1 else (None, None)


def with_catalogue(measurements: pd.DataFrame, catalogue: pd.DataFrame) -> pd.DataFrame:
    """Measurements plus indicator name/theme/unit/type/number, and an `indicator` text."""
    cols = [c for c in ["indicator_code", "indicator_naam", "thema", "eenheid", "indicator_type", "indicator_nummer"]
            if c in catalogue]
    df = measurements.merge(catalogue[cols].drop_duplicates("indicator_code"), on="indicator_code", how="left")
    df["indicator"] = df.get("thema", "").fillna("").astype(str) + " | " + df.get("indicator_naam", "").fillna("").astype(str)
    return df


def _num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", ".", regex=False), errors="coerce")


# --- statistics -------------------------------------------------------------------------------

def wilson(numerator: float, denominator: float, z: float = Z) -> tuple[float, float]:
    if denominator <= 0:
        return math.nan, math.nan
    p = numerator / denominator
    centre = (p + z * z / (2 * denominator)) / (1 + z * z / denominator)
    half = z * math.sqrt(p * (1 - p) / denominator + z * z / (4 * denominator * denominator)) / (1 + z * z / denominator)
    return max(0.0, centre - half), min(1.0, centre + half)


def funnel_verdicts(y: pd.Series, se: pd.Series, reference: float, direction: str | None,
                    winsor: float = 0.1) -> pd.Series:
    """'beter' / 'slechter' / 'gemiddeld' with overdispersion correction (Spiegelhalter 2005).

    Hospitals always differ somewhat beyond chance (registration, case mix). That between-hospital
    variance tau² is estimated from winsorised z-scores (DerSimonian-Laird) and added to each
    hospital's own sampling variance, so a verdict needs a difference larger than the usual spread.
    """
    out = pd.Series(None, index=y.index, dtype="object")
    ok = y.notna() & se.notna() & (se > 0)
    if direction not in ("lower_better", "higher_better") or pd.isna(reference) or ok.sum() == 0:
        return out
    y, se = y[ok].astype(float), se[ok].astype(float)
    z = (y - reference) / se
    n = len(z)
    if n >= MIN_UNITS_FOR_TAU:
        z = z.clip(z.quantile(winsor), z.quantile(1 - winsor))
        w = 1 / se ** 2
        phi = float((z ** 2).mean())
        tau2 = max(0.0, (n * phi - (n - 1)) / (w.sum() - (w ** 2).sum() / w.sum()))
    else:
        tau2 = 0.0  # the spread between hospitals cannot be estimated from a handful
    spread = (se ** 2 + tau2) ** 0.5
    higher_is_better = direction == "higher_better"
    z_up = Z_BETTER if higher_is_better else Z_WORSE      # threshold for a value above the reference
    z_down = Z_WORSE if higher_is_better else Z_BETTER    # threshold for a value below it
    out[ok] = "gemiddeld"
    out[(y > reference + z_up * spread)[lambda s: s].index] = "beter" if higher_is_better else "slechter"
    out[(y < reference - z_down * spread)[lambda s: s].index] = "slechter" if higher_is_better else "beter"
    return out


# --- 1. ratios --------------------------------------------------------------------------------

def _compare_ratios(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    num, den = _num(df["numerator"]) if "numerator" in df else np.nan, _num(df["denominator"]) if "denominator" in df else np.nan
    df["num"], df["den"] = num, den
    ratio = df["den"].gt(0) & df["num"].ge(0) & (df["num"] <= df["den"])
    totals = df[ratio].groupby(keys, dropna=False)[["num", "den"]].sum()
    df = df.join((totals["num"] / totals["den"]).rename("national_rate"), on=keys)
    bounds = [wilson(n, d) if r else (math.nan, math.nan) for n, d, r in zip(df["num"], df["den"], ratio)]
    df["rate"] = (df["num"] / df["den"]).where(ratio)
    df["ci_low"], df["ci_high"] = [b[0] for b in bounds], [b[1] for b in bounds]
    df["method"] = np.where(ratio, "ratio", None)
    df["verdict"] = np.where(df["direction"] == "volume", "volume", None)
    df["position"] = None

    judged = df["direction"].isin(["lower_better", "higher_better"])
    reported = judged & (ratio | _num(df["value"]).notna() if "value" in df else ratio)
    for _, group in df[judged].groupby(keys, dropna=False):
        idx = group.index
        if not ratio[idx].any():
            continue  # not a ratio indicator (e.g. a mean score): handled by _mean_scores
        coverage = ratio[idx].sum() / max(1, reported[idx].sum())
        if coverage < MIN_RATIO_COVERAGE:
            df.loc[idx, "position"] = "te weinig ziekenhuizen met teller/noemer: niet beoordeeld"
            df.loc[idx, "national_rate"] = np.nan
            continue
        rows = group[ratio[idx]]
        p0 = rows["national_rate"].iloc[0] if not rows.empty else np.nan
        y = np.arcsin(np.sqrt(rows["rate"]))
        se = 1 / (2 * np.sqrt(rows["den"]))
        df.loc[rows.index, "verdict"] = funnel_verdicts(y, se, np.arcsin(np.sqrt(p0)), rows["direction"].iloc[0])
    return df


# --- 2. published point + interval -------------------------------------------------------------

_ROLE = re.compile(r"(aantal \(n\)|gemiddelde|gecorrigeerd percentage|"
                   r"95\s*% betrouwbaarheidsinterval (?:lower|upper) bound)\.?\s*$", re.IGNORECASE)


def interval_role(text: object) -> tuple[str | None, str | None]:
    """(name without role phrase, role) for a row of a published point/interval group."""
    if not isinstance(text, str):
        return None, None
    clean = re.sub(r"\s+", " ", text.replace("_x000D_", " ")).strip()
    match = _ROLE.search(clean)
    if not match:
        return None, None
    phrase = match.group(1).lower()
    role = "n" if phrase.startswith("aantal") else "lower" if "lower" in phrase else "upper" if "upper" in phrase else "point"
    return clean[:match.start()].strip(" .|"), role


def scale_of(name: str) -> str | None:
    return next((s for s in _SCALES if s.lower() in name.lower()), None)


def interval_label(name: str) -> str:
    low, scale = name.lower(), scale_of(name)
    if "revisie" in low:
        horizon = re.search(r"binnen (\w+) jaar", name, re.IGNORECASE)
        return f"Revisie binnen {horizon.group(1) if horizon else '?'} jaar (gecorrigeerd)"
    if "preoperatieve" in low or "preoperatievescore" in low:
        return f"Score vóór de operatie: {scale or 'PROM'}"
    months = re.search(r"(\d+) maanden", name)
    return f"Verbetering volgens patiënt na {months.group(1) if months else '?'} mnd: {scale or 'PROM'}"


def interval_kind(name: str) -> str | None:
    """'revision' | 'prom12' | None (shown only)."""
    low = name.lower()
    if "revisie" in low:
        return "revision"
    if "verschilscore" in low and "12 maanden" in low:
        return "prom12"
    return None


def _implausible(name: str, point: float) -> bool:
    low = name.lower()
    limit = next((v for k, v in PLAUSIBLE_CHANGE.items() if k in low), None)
    return limit is not None and abs(point) > limit


def _compare_intervals(df: pd.DataFrame) -> pd.DataFrame:
    roles = df["indicator"].map(interval_role)
    df = df.assign(_name=[r[0] for r in roles], _role=[r[1] for r in roles])
    df = df[df["_role"].notna()].copy()
    if df.empty:
        return pd.DataFrame()
    # one published indicator = rows with the same number minus its last character (4d1a..d -> 4d1,
    # 5a1..3 -> 5a); names are spelled inconsistently in the source, so they are only a fallback
    if "indicator_nummer" in df:
        number = df["indicator_nummer"].astype(str).str.strip()
        df["_stem"] = (df.get("thema", "").fillna("").astype(str) + " #" + number.str[:-1]).where(
            df["indicator_nummer"].notna(), df["_name"])
    else:
        df["_stem"] = df["_name"]
    names = df[df["_role"] == "point"].groupby("_stem")["_name"].first()
    df["_v"] = _num(df["value"])
    keys = ["procedure_id", "location_key", "verslagjaar", "_stem"]
    wide = df.pivot_table(index=keys, columns="_role", values="_v", aggfunc="first").reset_index()
    codes = df[df["_role"] == "point"].drop_duplicates(keys).set_index(keys)["indicator_code"] \
        if "indicator_code" in df else pd.Series(dtype=object)
    if not {"point", "lower", "upper"} <= set(wide.columns):
        return pd.DataFrame()
    if "n" not in wide:
        wide["n"] = np.nan
    wide = wide.dropna(subset=["point", "lower", "upper"])
    # placeholders in the source mean 'no data'
    placeholder = (wide["n"] == 0) | ((wide["point"] == 0) & (wide["lower"] == 0) & (wide["upper"] == 0))
    wide = wide[~placeholder].copy()
    # repair swapped bounds when the point lies between them
    swapped = (wide["lower"] > wide["upper"]) & wide["point"].between(wide["upper"], wide["lower"])
    old_lower = wide.loc[swapped, "lower"].copy()
    wide.loc[swapped, "lower"] = wide.loc[swapped, "upper"]
    wide.loc[swapped, "upper"] = old_lower

    rows = []
    for (proc, stem, year), group in wide.groupby(["procedure_id", "_stem", "verslagjaar"], dropna=False):
        name = names.get(stem, stem)
        kind = interval_kind(name)
        problem = pd.Series(None, index=group.index, dtype="object")
        problem[~((group["lower"] <= group["point"]) & (group["point"] <= group["upper"]))] = "inconsistent in bron"
        problem[group["point"].map(lambda p: _implausible(name, p)) & problem.isna()] = "onwaarschijnlijke waarde in bron"
        if kind == "prom12":
            few = group["n"].isna() | (group["n"] < MIN_N_PROM)
            problem[few & problem.isna()] = f"minder dan {MIN_N_PROM} patiënten: niet beoordeeld"
        usable = group[problem.isna()]
        half = (usable["upper"] - usable["lower"]) / (2 * Z)
        if kind == "revision":
            w = 1 / half[half > 0] ** 2
            reference = float((usable.loc[w.index, "point"] * w).sum() / w.sum()) if len(w) else np.nan
            direction = "lower_better"
        elif kind == "prom12":
            reference = usable["point"].median()
            # change scores are stored as improvement (pain: before minus after), so higher is better;
            # a non-positive national median would mean the convention changed: then do not judge
            direction = "higher_better" if reference > 0 else None
        else:
            reference, direction = usable["point"].median(), None
        # the half of the published interval that faces the reference
        facing = np.where(usable["point"] <= reference, usable["upper"] - usable["point"],
                          usable["point"] - usable["lower"]) / Z
        se = pd.Series(np.where(facing > 0, facing, half), index=usable.index)
        verdicts = funnel_verdicts(usable["point"], se, reference, direction) if kind else pd.Series(dtype=object)
        for r in group.itertuples():
            verdict = verdicts.get(r.Index) if r.Index in verdicts.index else None
            code = codes.get((proc, r.location_key, year, stem)) if len(codes) else None
            rows.append({"procedure_id": proc, "location_key": r.location_key, "verslagjaar": year,
                         "indicator_code": code, "indicator": name, "indicator_nl": interval_label(name),
                         "direction": direction, "value": r.point, "rate": r.point, "ci_low": r.lower,
                         "ci_high": r.upper, "national_rate": reference, "n_waarnemingen": r.n,
                         "verdict": None if verdict is None or pd.isna(verdict) else verdict,
                         "method": "interval", "position": problem[r.Index]})
    return pd.DataFrame(rows)


def _prom_response_filter(df: pd.DataFrame) -> pd.DataFrame:
    """PROM verdicts need a known pre-operative PROM response of at least MIN_PROM_RESPONSE %."""
    response = df[df["indicator"].astype(str).str.contains("Responspercentage pre-operatief", case=False, na=False)]
    if response.empty:
        return df
    rate = _num(response["value"])
    good = {k for k, v in zip(zip(response["procedure_id"], response["location_key"], response["verslagjaar"]), rate)
            if pd.notna(v) and v >= MIN_PROM_RESPONSE}
    measured = set(zip(response["procedure_id"], response["verslagjaar"]))
    keys = list(zip(df["procedure_id"], df["location_key"], df["verslagjaar"]))
    is_prom = df["indicator_nl"].astype(str).str.startswith("Verbetering volgens patiënt") & df["verdict"].notna()
    applies = pd.Series([(k[0], k[2]) in measured and k not in good for k in keys], index=df.index)
    hit = is_prom & applies
    df.loc[hit, "verdict"] = None
    df.loc[hit, "position"] = f"PROM-respons onbekend of < {MIN_PROM_RESPONSE:.0f}%: niet beoordeeld"
    return df


# --- 3. means without spread (shown, never judged) ------------------------------------------------

def _mean_scores(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    value = _num(df["value"]) if "value" in df else pd.Series(math.nan, index=df.index)
    is_mean = (df["method"].isna() & value.notna() & df["direction"].isin(["lower_better", "higher_better"])
               & df["position"].isna())  # not for ratios already marked as not judgeable
    if "eenheid" in df:  # a percentage without numerator/denominator is not a mean score
        is_mean &= df["eenheid"].astype(str).str.lower().isin(["gemiddelde", "getal", "score", "nan", "none"])
    if not is_mean.any():
        return df
    weight = _num(df["n_waarnemingen"]).fillna(1.0) if "n_waarnemingen" in df else pd.Series(1.0, index=df.index)
    sub = df[is_mean].assign(_v=value[is_mean], _w=weight[is_mean])
    national = sub.assign(_vw=sub["_v"] * sub["_w"]).groupby(keys, dropna=False)[["_vw", "_w"]].sum()
    sub = sub.join((national["_vw"] / national["_w"]).rename("_m"), on=keys)
    favourable = (sub["_v"] > sub["_m"]) == (sub["direction"] == "higher_better")
    df.loc[is_mean, "rate"] = sub["_v"]
    df.loc[is_mean, "national_rate"] = sub["_m"]
    df.loc[is_mean, "method"] = "mean"
    df.loc[is_mean, "position"] = favourable.map({True: "gunstiger", False: "ongunstiger"}).where(sub["_v"] != sub["_m"], "gelijk")
    return df


# --- all together ------------------------------------------------------------------------------

def compare(quality: pd.DataFrame) -> pd.DataFrame:
    """One row per location × indicator with rate, interval, reference, verdict and method.

    Expects procedure_id, location_key, indicator (text), verslagjaar, numerator, denominator,
    value (and optionally indicator_code, indicator_nummer, eenheid, n_waarnemingen)."""
    if quality.empty:
        return pd.DataFrame()
    df = quality.copy()
    codes = df["indicator_code"] if "indicator_code" in df else pd.Series([None] * len(df), index=df.index)
    cache: dict[tuple, tuple] = {}

    def lookup(key: tuple) -> tuple:
        if key not in cache:  # one rule lookup per distinct indicator, not per row
            proc, text, code = key
            cache[key] = (None, None) if interval_role(text)[1] else direction_for(proc, text, code)
        return cache[key]
    meta = [lookup(k) for k in zip(df["procedure_id"], df["indicator"], codes)]
    df["direction"], df["indicator_nl"] = [m[0] for m in meta], [m[1] for m in meta]
    keys = ["procedure_id", "indicator_code" if "indicator_code" in df else "indicator", "verslagjaar"]
    df = _mean_scores(_compare_ratios(df, keys), keys).drop(columns=["num", "den"])
    intervals = _compare_intervals(df)
    if not intervals.empty:
        df = pd.concat([df, intervals], ignore_index=True)
    return _prom_response_filter(df)


# --- summary per domain ------------------------------------------------------------------------

DOMAINS = [  # (domain, indicator pattern, sentence when better, sentence when worse)
    ("heroperatie", r"revisie", "Minder heroperaties", "Meer heroperaties"),
    ("infectie", r"wondinfectie", "Minder infecties", "Meer infecties"),
    ("herstel", r"verbetering volgens patiënt", "Patiënten melden meer herstel", "Patiënten melden minder herstel"),
    ("zien", r"beter zien", "Vaker beter zicht na de operatie", "Minder vaak beter zicht"),
    ("sterkte", r"refractie", "Vaker de beoogde sterkte", "Minder vaak de beoogde sterkte"),
]


def domain_of(indicator_nl: object) -> str | None:
    text = str(indicator_nl).lower()
    return next((d for d, pattern, _, _ in DOMAINS if re.search(pattern, text)), None)


def domain_verdicts(rows: pd.DataFrame) -> dict[str, str]:
    """Verdict per domain for one location-year.

    A domain is 'beter' with at least one better and no worse indicator ('slechter' vice versa).
    The patient-reported domain needs the disease-specific scale (OHS/OKS) or at least two of
    the five correlated scales to agree, so one scale alone does not decide it."""
    out = {}
    for domain, _, _, _ in DOMAINS:
        sub = rows[rows["indicator_nl"].map(domain_of) == domain]
        verdicts = sub["verdict"].dropna()
        verdicts = verdicts[verdicts.isin(["beter", "slechter", "gemiddeld"])]
        if verdicts.empty:
            continue
        better, worse = (verdicts == "beter"), (verdicts == "slechter")
        if domain == "herstel":
            specific = sub.loc[verdicts.index, "indicator_nl"].astype(str).str.contains("|".join(_DISEASE_SPECIFIC))
            strong_better = (better & specific).any() or better.sum() >= 2
            strong_worse = (worse & specific).any() or worse.sum() >= 2
        else:
            strong_better, strong_worse = better.any(), worse.any()
        if strong_better and not worse.any():
            out[domain] = "beter"
        elif strong_worse and not better.any():
            out[domain] = "slechter"
        else:
            out[domain] = "gemiddeld"
    return out


def domain_highlights(rows: pd.DataFrame) -> list[tuple[str, str]]:
    """[(verdict, plain-language sentence)] for the domains that are clearly better or worse."""
    verdicts = domain_verdicts(rows)
    return [(verdicts[d], better if verdicts[d] == "beter" else worse)
            for d, _, better, worse in DOMAINS if verdicts.get(d) in ("beter", "slechter")]


def hospital_verdict(compared: pd.DataFrame, procedure_id: str) -> pd.DataFrame:
    """Per location (latest verslagjaar in `compared`): domain counts and one summary verdict.

    boven_gemiddeld: a domain better, none worse · onder_gemiddeld: the reverse · gemengd: both ·
    gemiddeld: only average domains · geen_data: no judged indicators."""
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
        domains = list(domain_verdicts(group).values())
        beter, slechter, gemiddeld = domains.count("beter"), domains.count("slechter"), domains.count("gemiddeld")
        verdict = ("gemengd" if beter and slechter else "boven_gemiddeld" if beter else
                   "onder_gemiddeld" if slechter else "gemiddeld" if gemiddeld else "geen_data")
        volume_rows = group[group["direction"] == "volume"]
        volume = _num(volume_rows["value"]).max() if not volume_rows.empty else math.nan
        rows.append({"location_key": location_key, "quality_verdict": verdict, "n_beter": beter,
                     "n_slechter": slechter, "n_gemiddeld": gemiddeld,
                     "verslagjaar": int(group["year"].max()) if group["year"].notna().any() else None,
                     "volume": volume})
    return pd.DataFrame(rows, columns=columns)
