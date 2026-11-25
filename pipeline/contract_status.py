"""Normalise contract status text from hospital PDFs and web pages.

Conservative by design: mixed signals or exception clauses ('m.u.v. budgetpolis') give
'onbekend', so a human reviews the cell instead of us storing a confident wrong answer.
"""

from __future__ import annotations

import re

STATUSES = ["gecontracteerd", "in_onderhandeling", "geen_contract", "onbekend"]

_NEGOTIATING = re.compile(
    r"onderhandel|in gesprek|\(?nog\)? geen contract|nog niet gecontracteerd|contract volgt|nog niet bekend|nog niet rond"
    r"|voorstel|vooruitgang|lopen nog|gesprekken")
_NEGATIVE = re.compile(r"niet gecontracteerd|ongecontracteerd|geen contract|opgezegd|beeindigd|beëindigd")
_POSITIVE = re.compile(
    r"(?<!niet )(?<!on)gecontracteerd|(?<!geen )contract afgesloten|heeft contract|met contract|wel contract"
    r"|contract getekend|contract rond|contract \d{4} rond|akkoord|hebben (?:een )?contract|contract hebben")
_EXCEPTION = re.compile(r"m\.? ?u\.? ?v\.?|behalve|uitgezonderd|uitzondering|\bwel voor\b")
_YES = {"ja", "j", "v", "x", "✓", "✔", "yes"}
_NO = {"nee", "n", "-", "–", "✗", "✘", "no"}
_FOOTNOTE = re.compile(r"[*¹²³⁴⁵⁶⁷⁸⁹⁰†]+|\(\d+\)")
_PLAFOND_CLAUSE = re.compile(r"(?:(?:met|zonder|geen|incl\.?|inclusief)\s+)?(?:omzet|zorg)?plafond\s*[:=]?\s*(?:ja|nee|n\.?v\.?t\.?|geen)?")
_NO_PLAFOND = re.compile(r"(geen|zonder) (omzet|zorg)?plafond|plafond\s*[:=]?\s*(nee|n\.?v\.?t\.?|geen)\b")


def clean(text: object) -> str:
    """Lowercase; drop footnote markers; collapse whitespace, hyphens and no-break spaces."""
    if not isinstance(text, str):
        return ""
    text = _FOOTNOTE.sub(" ", text.lower())
    return re.sub(r"[\s\- ]+", " ", text).strip(" .,;:")


def status_from_text(text: object) -> str:
    value = clean(_PLAFOND_CLAUSE.sub(" ", clean(text)))
    if not value:
        return "onbekend"
    if value in _YES:
        return "gecontracteerd"
    if value in _NO:
        return "geen_contract"
    first = value.split(" ")[0].strip(",")
    if _NEGOTIATING.search(value):
        return "in_onderhandeling"
    negative = bool(_NEGATIVE.search(value)) or first in _NO
    positive = bool(_POSITIVE.search(value)) or first in _YES
    if (negative and positive) or ((negative or positive) and _EXCEPTION.search(value)):
        return "onbekend"  # mixed or partial (e.g. not for the budget policy): needs a human
    if negative:
        return "geen_contract"
    if positive:
        return "gecontracteerd"
    return "onbekend"


def plafond_from_text(text: object, plafond_column: bool = False) -> bool | None:
    """True/False when the text says whether an omzetplafond applies, else None.

    With plafond_column=True the cell sits under (or next to) an 'omzetplafond' header,
    so a bare 'ja'/'nee'/'x' answers the question and an empty cell means 'no ceiling'.
    """
    value = clean(text)
    if not value:
        return False if plafond_column else None
    if _NO_PLAFOND.search(value):
        return False
    if "plafond" in value:
        return True
    if plafond_column:
        if value in _YES:
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


def combine_plafond(values: list[bool | None]) -> bool | None:
    known = {v for v in values if v is not None}
    return known.pop() if len(known) == 1 else None
