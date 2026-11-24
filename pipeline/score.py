"""Combine hospitals, contracts, policies, waiting times and quality into a per-policy overview.

Deliberately no single ranking score: the app shows counts and per-hospital facts with
source and peildatum, because hospital rankings are often misleading (small numbers, case mix).
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from pipeline.reference import MANUAL, PROCESSED, hospitals, labels

ACCESS_ORDER = ["gecontracteerd", "gecontracteerd_met_plafond", "in_onderhandeling", "geen_contract", "onbekend"]


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
    if not policies.empty:
        return policies
    fallback = labels()[["concern", "label"]].copy()
    fallback["polis"] = fallback["label"] + " (polissen nog niet ingevoerd)"
    fallback["polis_type"] = None
    fallback["premie_per_maand"] = None
    fallback["vergoeding_niet_gecontracteerd_pct"] = None
    fallback["year"] = year
    return fallback


def load_contracts(year: int = 2027) -> pd.DataFrame:
    contracts = _read(MANUAL / "contracts.csv")
    if contracts.empty:
        return contracts
    return contracts[contracts["year"] == year]


def contract_for(contracts: pd.DataFrame, location_id: str, concern: str, label: str) -> dict | None:
    """Most specific contract row: the label's own row first, else the concern-wide row (label empty).

    When several rows match (history), the latest peildatum wins.
    """
    if contracts.empty:
        return None
    rows = contracts[(contracts["location_id"] == location_id) & (contracts["concern"] == concern)]
    own = rows[rows["label"] == label]
    concern_wide = rows[rows["label"].isna() | (rows["label"] == "")]
    for candidate in (own, concern_wide):
        if not candidate.empty:
            return candidate.sort_values("peildatum", na_position="first").iloc[-1].to_dict()
    return None


def access_status(policy: dict, contract: dict | None) -> str:
    if str(policy.get("polis_type") or "").lower() == "restitutie":
        return "gecontracteerd"  # restitutie: market-rate reimbursement everywhere
    if not contract:
        return "onbekend"
    status = contract.get("status", "onbekend")
    if status == "gecontracteerd" and str(contract.get("omzetplafond")).lower() in {"true", "1", "ja"}:
        return "gecontracteerd_met_plafond"
    return status if status in ACCESS_ORDER else "onbekend"


def latest_waits(procedure_id: str, waits: pd.DataFrame | None = None) -> pd.DataFrame:
    """Waiting time in weeks per location for the procedure, latest peildatum, treatment wait preferred."""
    waits = _read(PROCESSED / "waiting_times.csv") if waits is None else waits
    if waits.empty:
        return pd.DataFrame(columns=["location_id", "weeks", "wait_type", "peildatum"])
    sub = waits[(waits["procedure_id"] == procedure_id) & waits["location_id"].notna()].copy()
    if "wait_type" in sub and sub["wait_type"].notna().any():
        treatment = sub[sub["wait_type"].fillna("").str.contains("behandel", case=False)]
        if not treatment.empty:
            sub = treatment
    sub = sub.sort_values("peildatum", na_position="first")
    latest = sub.groupby("location_id").tail(1)
    return latest[["location_id", "weeks", "wait_type", "peildatum"]]


def quality_counts(procedure_id: str, quality: pd.DataFrame | None = None) -> pd.DataFrame:
    """Number of published indicators per location for the procedure (latest verslagjaar)."""
    quality = _read(PROCESSED / "quality.csv") if quality is None else quality
    if quality.empty:
        return pd.DataFrame(columns=["location_id", "indicators", "verslagjaar"])
    sub = quality[(quality["procedure_id"] == procedure_id) & quality["location_id"].notna()].copy()
    if sub.empty:
        return pd.DataFrame(columns=["location_id", "indicators", "verslagjaar"])
    sub["verslagjaar"] = sub["verslagjaar"].astype(str)
    latest_year = sub.groupby("location_id")["verslagjaar"].transform("max")
    sub = sub[sub["verslagjaar"] == latest_year]
    return sub.groupby("location_id").agg(indicators=("indicator", "nunique"), verslagjaar=("verslagjaar", "first")).reset_index()


def overview(lat: float, lon: float, procedure_id: str, radius_km: float = 25, year: int = 2027,
             policies: pd.DataFrame | None = None, contracts: pd.DataFrame | None = None,
             waits: pd.DataFrame | None = None, quality: pd.DataFrame | None = None,
             hospital_table: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (per_policy summary, per_policy × hospital detail)."""
    near = hospitals_within(lat, lon, radius_km, hospital_table)
    policies = load_policies(year) if policies is None else policies
    contracts = load_contracts(year) if contracts is None else contracts
    near = near.merge(latest_waits(procedure_id, waits), on="location_id", how="left")
    near = near.merge(quality_counts(procedure_id, quality), on="location_id", how="left")

    detail_rows = []
    for policy in policies.to_dict("records"):
        for hosp in near.to_dict("records"):
            contract = contract_for(contracts, hosp["location_id"], policy["concern"], policy["label"])
            detail_rows.append({
                "concern": policy["concern"], "label": policy["label"], "polis": policy["polis"],
                "location": hosp["location_name"], "distance_km": round(hosp["distance_km"], 1),
                "access": access_status(policy, contract),
                "contract_peildatum": (contract or {}).get("peildatum"),
                "contract_source": (contract or {}).get("source_url") or (contract or {}).get("source"),
                "wait_weeks": hosp.get("weeks"), "wait_peildatum": hosp.get("peildatum"),
                "quality_indicators": hosp.get("indicators"), "quality_year": hosp.get("verslagjaar"),
            })
    detail = pd.DataFrame(detail_rows)
    if detail.empty:
        return pd.DataFrame(), detail

    def summarise(group: pd.DataFrame) -> pd.Series:
        contracted = group["access"].isin(["gecontracteerd", "gecontracteerd_met_plafond"])
        waits_ok = group.loc[contracted, "wait_weeks"].dropna()
        return pd.Series({
            "ziekenhuizen_in_bereik": len(group),
            "gecontracteerd": int((group["access"] == "gecontracteerd").sum()),
            "met_omzetplafond": int((group["access"] == "gecontracteerd_met_plafond").sum()),
            "in_onderhandeling": int((group["access"] == "in_onderhandeling").sum()),
            "geen_contract": int((group["access"] == "geen_contract").sum()),
            "onbekend": int((group["access"] == "onbekend").sum()),
            "kortste_wachttijd_gecontracteerd_weken": waits_ok.min() if not waits_ok.empty else None,
        })

    summary = detail.groupby(["concern", "label", "polis"], sort=False).apply(summarise, include_groups=False).reset_index()
    summary = summary.merge(policies[["polis", "polis_type", "premie_per_maand"]], on="polis", how="left")
    return summary, detail
