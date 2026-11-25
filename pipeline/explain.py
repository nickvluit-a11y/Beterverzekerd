"""Turn quality comparisons into short sentences a patient understands.

'1.81 vs 0.64, gemiddeld' becomes 'Heroperatie binnen 1 jaar: 1,8 op de 100 patiënten (landelijk 0,6).
Niet duidelijk anders: te weinig patiënten om zeker te zijn.'
"""

from __future__ import annotations

import pandas as pd

# PROM scales: what one point means, and whether the change is a rise or a fall for the patient
_SCALES = {
    "algemene gezondheid": ("verbeterde met {v} (schaal 0 tot 1)", 2),
    "eigen gezondheidscijfer": ("steeg met {v} punten (schaal 0 tot 100)", 0),
    "functie van de heup": ("verbeterde met {v} punten (schaal 0 tot 48)", 0),
    "functie van de knie": ("verbeterde met {v} punten (schaal 0 tot 48)", 0),
    "pijn in rust": ("daalde met {v} punten (schaal 0 tot 10)", 1),
    "pijn bij bewegen": ("daalde met {v} punten (schaal 0 tot 10)", 1),
}


def nl(value: float, decimals: int = 1) -> str:
    return f"{value:.{decimals}f}".replace(".", ",")


def _short_name(indicator: str) -> str:
    return (indicator.replace("Verbetering volgens patiënt na 12 maanden: ", "")
            .replace("Heroperatie (revisie)", "Heroperatie"))


def verdict_text(verdict: str | None, rate: float, national: float) -> tuple[str, str]:
    """(css class, plain verdict) — 'gemiddeld' explains why a big gap is still not a verdict."""
    if verdict == "beter":
        return "beter", "✓ beter dan gemiddeld"
    if verdict == "slechter":
        return "slechter", "✗ slechter dan gemiddeld"
    if pd.notna(rate) and pd.notna(national) and national and abs(rate - national) / abs(national) > 0.3:
        return "avg", "niet duidelijk anders: te weinig patiënten om zeker te zijn"
    return "avg", "rond het gemiddelde"


def explain(row: dict) -> tuple[str, str, str]:
    """(plain name, what was measured, (css, verdict text)) for one judged indicator row."""
    name = str(row.get("indicator") or "")
    rate, national, method = row.get("rate"), row.get("national_rate"), row.get("method")
    short = _short_name(name)
    if method == "ratio":  # fraction of patients
        rate, national = rate * 100, national * 100
    scale = next((s for s in _SCALES if s in name), None)
    if scale and "Verbetering" in name:
        template, decimals = _SCALES[scale]
        measured = (f"Patiënten: {short} " + template.format(v=nl(rate, decimals))
                    + f" (landelijk {nl(national, decimals)})")
        title = "Herstel volgens patiënten"
    else:
        measured = f"{nl(rate)} op de 100 patiënten (landelijk {nl(national)})"
        title = short
    return title, measured, verdict_text(row.get("verdict"), rate, national)


def trend_sentences(trend: pd.DataFrame, min_years: int = 3) -> list[str]:
    """'Al 3 jaar beter op: Diepe wondinfectie' when the latest years agree."""
    out = []
    if trend.empty:
        return out
    for indicator, group in trend.dropna(subset=["verdict"]).groupby("indicator"):
        recent = group.sort_values("verslagjaar")["verdict"].tolist()[-min_years:]
        if len(recent) == min_years and len(set(recent)) == 1 and recent[0] in ("beter", "slechter"):
            out.append(f"Al {min_years} jaar {recent[0]} dan gemiddeld op: {_short_name(indicator).lower()}")
    return out
