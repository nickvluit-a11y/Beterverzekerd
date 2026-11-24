"""Normalise contract status text from hospital PDFs and insurer care finders.

Conservative by design: when a cell contains both a positive and a negative signal,
the result is 'onbekend' so a human reviews it, rather than a confident wrong answer.
"""

from __future__ import annotations

import re

STATUSES = ["gecontracteerd", "in_onderhandeling", "geen_contract", "onbekend"]

_NEGOTIATING = re.compile(r"onderhandel|\(?nog\)? geen contract|contract volgt|nog niet bekend")
_NEGATIVE = re.compile(r"niet gecontracteerd|ongecontracteerd|geen contract|contract opgezegd|opgezegd|beeindigd|beëindigd")
_POSITIVE = re.compile(r"(?<!niet )(?<!on)gecontracteerd|contract afgesloten|heeft contract|met contract")
_YES = {"ja", "v", "✓", "✔", "j", "yes"}
_NO = {"nee", "n", "-", "–", "✗", "✘", "no"}
_PLAFOND_CLAUSE = re.compile(r"(omzet|zorg)?plafond\s*[:=]?\s*(ja|nee|n\.?v\.?t\.?|geen)?")
_NO_PLAFOND = re.compile(r"(geen|zonder) (omzet|zorg)?plafond|plafond\s*[:=]?\s*(nee|n\.?v\.?t\.?|geen)\b")


def clean(text: object) -> str:
    """Lowercase, and collapse whitespace, hyphens and no-break spaces into single spaces."""
    if text is None or (isinstance(text, float) and text != text):
        return ""
    return re.sub(r"[\s\- ]+", " ", str(text).lower()).strip(" .,;:")


def status_from_text(text: object) -> str:
    value = clean(_PLAFOND_CLAUSE.sub(" ", clean(text)))
    if not value:
        return "onbekend"
    if value in _YES:
        return "gecontracteerd"
    if value in _NO:
        return "geen_contract"
    if _NEGOTIATING.search(value):
        return "in_onderhandeling"
    negative, positive = bool(_NEGATIVE.search(value)), bool(_POSITIVE.search(value))
    if negative and positive:
        return "onbekend"  # e.g. 'gecontracteerd, geen contract voor budgetpolis'
    if negative:
        return "geen_contract"
    if positive:
        return "gecontracteerd"
    return "onbekend"


def plafond_from_text(text: object, plafond_column: bool = False) -> bool | None:
    """True/False when the text says whether an omzetplafond applies, else None.

    With plafond_column=True the cell sits under an 'omzetplafond' header, so a bare
    'ja'/'nee'/'x' answers the question.
    """
    value = clean(text)
    if not value:
        return False if plafond_column else None
    if _NO_PLAFOND.search(value):
        return False
    if "plafond" in value:
        return True
    if plafond_column:
        if value in _YES or value == "x":
            return True
        if value in _NO or value in {"n.v.t", "nvt", "geen"}:
            return False
    return None


def normalise_status(text: object) -> tuple[str, bool | None]:
    """(status, omzetplafond) for one free-text cell. A ceiling implies a contract."""
    status, plafond = status_from_text(text), plafond_from_text(text)
    if status == "onbekend" and plafond is True:
        status = "gecontracteerd"
    return status, plafond


def combine(statuses: list[str]) -> str:
    """One status from several cells: conflicting signals give 'onbekend'."""
    known = {s for s in statuses if s != "onbekend"}
    return known.pop() if len(known) == 1 else "onbekend"
