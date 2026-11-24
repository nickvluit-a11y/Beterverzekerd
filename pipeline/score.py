"""Combine hospitals, contracts, policies, waiting times and quality into a per-policy overview.

Deliberately no single ranking score: the app shows counts and per-hospital facts with
source and peildatum, because hospital rankings are often misleading (small numbers, case mix).
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import pandas as pd

from pipeline.reference import MANUAL, PROCESSED, hospitals, labels

# vrije_keuze: restitutie policy, reimbursed up to market rate everywhere, but not a contract
ACCESS_ORDER = ["gecontracteerd", "gecontracteerd_met_plafond", "vrije_keuze", "in_onderhandeling", "geen_contract", "onbekend"]
POLICY_KEY = ["concern", "label", "polis"]

_MONTHS = {m: i for i, m in enumerate(
    ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus",
     "september", "oktober", "november", "december"], start=1)}


def to_date(value: object) -> pd.Timestamp:
    """Parse ISO dates, dd-mm-yyyy and '15 november 2026'. Unparseable -> NaT."""
    if not isinstance(value, str) or not value.strip():
        return pd.NaT
    text = value.strip().lower()
    match = re.fullmatch(r"(\d{1,2})[ \-/]([a-z]+)[ \-/](\d{4})", text)
    if match and match.group(2) in _MONTHS:
        return pd.Timestamp(int(match.group(3)), _MONTHS[match.group(2)], int(match.group(1)))
    iso = re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", text)
    return pd.to_datetime(text, dayfirst=not iso, errors="coerce")


def truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value == value and value == 1  # NaN-safe
    return str(value).strip().lower() in {"true", "1", "1.0", "ja", "yes"}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def hospitals_within(lat: float, lon: float, radius_km: float, table: pd.DataFrame | None = None) -> pd.DataFrame:
    table = (hospitals() if table is None else table).copy()
    table = table.dropna(subset=["lat", "lon"])
    table["distance_km"] = [haversine_km(lat, lon, a, b) for a, b in zip(table["lat"], table["lon"])]
    return table[table["distance_km"] <= radius_km].sort_values("distance_km").reset_index(drop=True)


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def load_policies(year: int = 2027) -> pd.DataFrame:
    """Policies for `year`. Without a filled policy file, fall back to one row per label."""
    policies = _read(MANUAL / f"polissen_{year}.csv")
    if policies.empty:
        policies = labels()[["concern", "label"]].copy()
        policies["polis"] = "(polissen nog niet ingevoerd)"
        policies["polis_type"] = None
        policies["premie_per_maand"] = None
        policies["year"] = year
    return policies


def load_contracts(year: int = 2027) -> pd.DataFrame:
    contracts = _read(MANUAL / "contracts.csv")
    return contracts if contracts.empty else contracts[contracts["year"] == year]


def contract_for(contracts: pd.DataFrame, location_id: str, concern: str, label: str) -> dict | None:
    """Most specific contract row: the label's own rows first, else concern-wide rows (label empty).

    A label-specific row always wins over a concern-wide one, because labels can have their own
    contract terms (e.g. budget labels). Within that level the latest peildatum wins (history).
    """
    if contracts.empty:
        return None
    rows = contracts[(contracts["location_id"] == location_id) & (contracts["concern"] == concern)]
    own = rows[rows["label"] == label]
    concern_wide = rows[rows["label"].isna() | (rows["label"] == "")]
    for candidate in (own, concern_wide):
        if not candidate.empty:
            order = candidate["peildatum"].map(to_date)
            return candidate.loc[order.sort_values(na_position="first").index[-1]].to_dict()
    return None


def access_status(policy: dict, contract: dict | None) -> str:
    if "restitutie" in str(policy.get("polis_type") or "").lower():
        return "vrije_keuze"
    if not contract:
        return "onbekend"
    status = contract.get("status", "onbekend")
    if status == "gecontracteerd" and truthy(contract.get("omzetplafond")):
        return "gecontracteerd_met_plafond"
    return status if status in ACCESS_ORDER else "onbekend"


def latest_waits(procedure_id: str, waits: pd.DataFrame | None = None) -> pd.DataFrame:
    """Waiting time in weeks per location: latest peildatum; per location the treatment wait
    ('behandeling') is preferred when that location reports one."""
    columns = ["location_id", "weeks", "wait_type", "peildatum"]
    waits = _read(PROCESSED / "waiting_times.csv") if waits is None else waits
    if waits.empty:
        return pd.DataFrame(columns=columns)
    sub = waits[(waits["procedure_id"] == procedure_id) & waits["location_id"].notna()].copy()
    if sub.empty:
        return pd.DataFrame(columns=columns)
    wait_type = sub["wait_type"] if "wait_type" in sub else pd.Series("", index=sub.index)
    sub["is_treatment"] = wait_type.fillna("").astype(str).str.contains("behandel", case=False)
    sub["date"] = sub["peildatum"].map(to_date) if "peildatum" in sub else pd.NaT
    sub = sub.sort_values(["location_id", "is_treatment", "date"], na_position="first")
    return sub.groupby("location_id").tail(1)[columns].reset_index(drop=True)


def quality_counts(procedure_id: str, quality: pd.DataFrame | None = None) -> pd.DataFrame:
    """Number of published indicators per location for the procedure (latest verslagjaar)."""
    columns = ["location_id", "indicators", "verslagjaar"]
    quality = _read(PROCESSED / "quality.csv") if quality is None else quality
    if quality.empty:
        return pd.DataFrame(columns=columns)
    sub = quality[(quality["procedure_id"] == procedure_id) & quality["location_id"].notna()].copy()
    sub["verslagjaar"] = pd.to_numeric(sub["verslagjaar"], errors="coerce").astype("Int64")
    sub = sub.dropna(subset=["verslagjaar"])
    if sub.empty:
        return pd.DataFrame(columns=columns)
    sub = sub[sub["verslagjaar"] == sub.groupby("location_id")["verslagjaar"].transform("max")]
    return sub.groupby("location_id").agg(indicators=("indicator", "nunique"), verslagjaar=("verslagjaar", "first")).reset_index()


def policy_name(policy: dict) -> str:
    """Unique display name: label + polis."""
    return f"{policy['label']} – {policy['polis']}"


def overview(lat: float, lon: float, procedure_id: str, radius_km: float = 25, year: int = 2027,
             policies: pd.DataFrame | None = None, contracts: pd.DataFrame | None = None,
             waits: pd.DataFrame | None = None, quality: pd.DataFrame | None = None,
             hospital_table: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (per-policy summary, per-policy × hospital detail). Both carry a unique `naam` column."""
    near = hospitals_within(lat, lon, radius_km, hospital_table)
    policies = load_policies(year) if policies is None else policies
    contracts = load_contracts(year) if contracts is None else contracts
    near = near.merge(latest_waits(procedure_id, waits), on="location_id", how="left")
    near = near.merge(quality_counts(procedure_id, quality), on="location_id", how="left")

    detail_rows = []
    for policy in policies.to_dict("records"):
        for hosp in near.to_dict("records"):
            contract = contract_for(contracts, hosp["location_id"], policy["concern"], policy["label"]) or {}
            detail_rows.append({
                "naam": policy_name(policy), "concern": policy["concern"], "label": policy["label"], "polis": policy["polis"],
                "location": hosp["location_name"], "distance_km": round(hosp["distance_km"], 1),
                "access": access_status(policy, contract or None),
                "contract_peildatum": contract.get("peildatum"),
                "contract_source": contract.get("source_url") or contract.get("source"),
                "wait_weeks": hosp.get("weeks"), "wait_peildatum": hosp.get("peildatum"),
                "quality_indicators": hosp.get("indicators"), "quality_year": hosp.get("verslagjaar"),
            })
    detail = pd.DataFrame(detail_rows)
    if detail.empty:
        return pd.DataFrame(), detail

    def summarise(group: pd.DataFrame) -> pd.Series:
        access = group["access"]
        reachable = access.isin(["gecontracteerd", "gecontracteerd_met_plafond", "vrije_keuze"])
        waits_ok = group.loc[reachable, "wait_weeks"].dropna()
        return pd.Series({
            "ziekenhuizen_in_bereik": len(group),
            "gecontracteerd": int((access == "gecontracteerd").sum()),
            "met_omzetplafond": int((access == "gecontracteerd_met_plafond").sum()),
            "vrije_keuze": int((access == "vrije_keuze").sum()),
            "in_onderhandeling": int((access == "in_onderhandeling").sum()),
            "geen_contract": int((access == "geen_contract").sum()),
            "onbekend": int((access == "onbekend").sum()),
            "kortste_wachttijd_weken": waits_ok.min() if not waits_ok.empty else None,
        })

    summary = (detail.groupby(["naam"] + POLICY_KEY, sort=False, dropna=False)
               .apply(summarise, include_groups=False).reset_index())
    extra = [c for c in ["polis_type", "premie_per_maand"] if c in policies]
    summary = summary.merge(policies[POLICY_KEY + extra].drop_duplicates(POLICY_KEY), on=POLICY_KEY, how="left")
    return summary, detail
