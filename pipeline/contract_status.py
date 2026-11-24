"""Normalise contract status text from hospital PDFs and insurer care finders."""

from __future__ import annotations

import re

# Ordered: the first matching pattern wins, so specific phrases come before general ones.
STATUSES = ["gecontracteerd", "in_onderhandeling", "geen_contract", "onbekend"]

_RULES: list[tuple[str, str]] = [
    (r"\bin onderhandeling\b|\bonderhandelingen\b|nog geen contract|\(nog\) geen contract", "in_onderhandeling"),
    (r"\bgeen contract\b|niet gecontracteerd|\bongecontracteerd\b|\bnee\b|^\s*[-x✗]\s*$", "geen_contract"),
    (r"\bgecontracteerd\b|\bcontract\b|\bja\b|^\s*[v✓✔]\s*$", "gecontracteerd"),
]
_PLAFOND = re.compile(r"omzetplafond|zorgplafond|\bplafond\b", re.IGNORECASE)
_NO_PLAFOND = re.compile(r"(geen|zonder) (omzet|zorg)?plafond", re.IGNORECASE)


def normalise_status(text: str | None) -> tuple[str, bool | None]:
    """Return (status, omzetplafond) for a free-text cell.

    omzetplafond is True/False when the text says so, otherwise None (unknown).
    """
    if text is None or not str(text).strip():
        return "onbekend", None
    value = str(text).strip().lower()
    status = "onbekend"
    for pattern, result in _RULES:
        if re.search(pattern, value):
            status = result
            break
    if _NO_PLAFOND.search(value):
        plafond: bool | None = False
    elif _PLAFOND.search(value):
        plafond = True
        if status == "onbekend":
            status = "gecontracteerd"  # a ceiling only exists within a contract
    else:
        plafond = None
    return status, plafond
