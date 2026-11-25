"""Combine hospitals, contracts, policies, waiting times and quality into a per-policy overview.

Deliberately no single ranking score: the app shows counts and per-hospital facts with
source and peildatum, because hospital rankings are often misleading (small numbers, case mix).
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import pandas as pd

from pipeline.quality import compare, hospital_verdict, with_catalogue
from pipeline.reference import MANUAL, PROCESSED, hospitals, indicator_catalogue, labels, locations

# vrije_keuze: restitutie policy, reimbursed up to market rate everywhere, but not a contract
ACCESS_ORDER = ["gecontracteerd", "gecontracteerd_met_plafond", "vergoed_als_contract", "vrije_keuze", "in_onderhandeling", "geen_contract", "onbekend"]
POLICY_KEY = ["concern", "label", "polis"]

_MONTH_NAMES = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus",
                "september", "oktober", "november", "december"]
_MONTHS = {m: i for i, m in enumerate(_MONTH_NAMES, start=1)}
_MONTHS.update({m[:3]: i for m, i in _MONTHS.copy().items()})
_MONTHS.update({"mrt": 3, "sept": 9})


def to_date(value: object) -> pd.Timestamp:
    """Parse ISO dates (also with '/'), dd-mm-yyyy and '15 november 2026' / '1 okt. 2026'. Unparseable -> NaT."""
    if isinstance(value, pd.Timestamp):
        return value
    if not isinstance(value, str) or not value.strip():
        return pd.NaT
    text = value.strip().lower()
    match = re.fullmatch(r"(\d{1,2})[ \-/]([a-z]+)\.?[ \-/](\d{4})", text)
    if match:
        month = _MONTHS.get(match.group(2))
        return pd.Timestamp(int(match.group(3)), month, int(match.group(1))) if month else pd.NaT
    year_first = re.fullmatch(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})(?:[ t].*)?", text)
    if year_first:
        y, m, d = map(int, year_first.groups())
        try:
            return pd.Timestamp(y, m, d)
        except ValueError:
            return pd.NaT
    return pd.to_datetime(text, dayfirst=True, errors="coerce")


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


def location_key(agb_code: object, postcode: object) -> str | None:
    """Same key as the Zorginzicht ingest: organisation AGB + postcode without space."""
    if not isinstance(agb_code, str) or not agb_code.strip():
        return None
    pc = postcode.replace(" ", "").upper() if isinstance(postcode, str) else ""
    return f"{agb_code.strip().zfill(8)}-{pc}"


def manual_locations() -> pd.DataFrame:
    """hospitals.csv in the shape of the national locations table (fallback before data exists)."""
    table = hospitals().copy()
    table["location_key"] = [location_key(a, p) or f"manual-{i}" for a, p, i in
                             zip(table["agb_code"], table["postcode"], table["location_id"])]
    table["organisatie_agb"] = table["agb_code"]
    return table


def candidate_locations(procedure_id: str, measurements: pd.DataFrame) -> pd.DataFrame:
    """Locations that perform the procedure (they report indicators for it) and have coordinates.

    Uses the national Zorginzicht locations when available, else the hand-made hospitals.csv."""
    national = locations()
    if not national.empty and not measurements.empty:
        performing = set(measurements.loc[measurements["procedure_id"] == procedure_id, "location_key"])
        table = national[national["location_key"].isin(performing)].copy()
        table["location_name"] = table["locatie_naam"].fillna(table["organisatie_naam"])
        table["location_name"] = table["location_name"] + " (" + table["plaats"].fillna("") + ")"
        return table
    return manual_locations()


def attach_organisation(contracts: pd.DataFrame) -> pd.DataFrame:
    """Contracts are agreed per organisation: add its AGB code via hospitals.csv."""
    if contracts.empty or "organisatie_agb" in contracts:
        return contracts
    agb_by_location = dict(zip(hospitals()["location_id"], hospitals()["agb_code"]))
    return contracts.assign(organisatie_agb=contracts["location_id"].map(agb_by_location))


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
    check = _read(PROCESSED / "premium_check.csv")
    if not check.empty and {"label", "polis", "confirmed"} <= set(check.columns):
        check = check[["label", "polis", "confirmed", "confirmed_url", "checked_on"]].drop_duplicates(["label", "polis"])
        check["confirmed"] = check["confirmed"].astype(str).str.lower() == "true"
        policies = policies.merge(check, on=["label", "polis"], how="left")
        policies["confirmed"] = policies["confirmed"].map(lambda v: bool(v) if pd.notna(v) else False).astype(object)
    else:
        policies["confirmed"] = None  # not checked yet: say nothing rather than 'unconfirmed'
    return policies


def load_contracts(year: int = 2027, include_candidates: bool = True) -> pd.DataFrame:
    """Contracts for `year`: rows checked by hand (data/manual/contracts.csv) first; for other
    organisation × concern × label combinations, rows read automatically from the hospital's own
    publication (data/processed/contracts_candidates.csv). Column `checked` tells them apart."""
    checked = attach_organisation(_read(MANUAL / "contracts.csv"))
    if not checked.empty:
        checked = checked[pd.to_numeric(checked["year"], errors="coerce") == year].assign(checked=True)
    if not include_candidates:
        return checked
    result = checked
    # the insurer's own care finder first (it decides what it reimburses), then the hospital's publication
    for name, origin in (("contracts_insurer.csv", "verzekeraar"), ("contracts_candidates.csv", "ziekenhuis")):
        auto = _read(PROCESSED / name)
        if auto.empty or "organisatie_agb" not in auto:
            continue
        auto = auto[(pd.to_numeric(auto["year"], errors="coerce") == year) & auto["organisatie_agb"].notna()
                    & (auto["status"] != "onbekend")].assign(checked=False, origin=origin)
        auto["organisatie_agb"] = auto["organisatie_agb"].astype(str).str.zfill(8)
        if not result.empty:
            done = set(zip(result["organisatie_agb"], result["concern"], result["label"].fillna("")))
            auto = auto[[k not in done for k in zip(auto["organisatie_agb"], auto["concern"], auto["label"].fillna(""))]]
        result = pd.concat([result, auto], ignore_index=True) if not result.empty else auto.reset_index(drop=True)
    return result


def contract_for(contracts: pd.DataFrame, organisatie_agb: str, concern: str, label: str) -> dict | None:
    """Most specific contract row: the label's own rows first, else concern-wide rows (label empty).

    A label-specific row always wins over a concern-wide one, because labels can have their own
    contract terms (e.g. budget labels). Within that level the latest peildatum wins (history).
    """
    if contracts.empty:
        return None
    rows = contracts[(contracts["organisatie_agb"] == organisatie_agb) & (contracts["concern"] == concern)]
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
    columns = ["location_key", "weeks", "wait_type", "peildatum"]
    waits = _read(PROCESSED / "waiting_times.csv") if waits is None else waits
    if waits.empty or "location_key" not in waits:
        return pd.DataFrame(columns=columns)
    sub = waits[(waits["procedure_id"] == procedure_id) & waits["location_key"].notna()].copy()
    if "insufficient" in sub:  # the NZa flags waits based on too few observations
        sub = sub[~sub["insufficient"].astype(str).str.lower().isin(["true", "1"])]
    if sub.empty:
        return pd.DataFrame(columns=columns)
    sub = sub[pd.to_numeric(sub["weeks"], errors="coerce").notna()]
    wait_type = sub["wait_type"] if "wait_type" in sub else pd.Series("", index=sub.index)
    sub["is_treatment"] = wait_type.fillna("").astype(str).str.contains("behandel", case=False)
    sub["date"] = sub["peildatum"].map(to_date) if "peildatum" in sub else pd.NaT
    # latest peildatum per location first, then prefer the treatment wait within it
    latest = sub.groupby("location_key")["date"].transform("max")
    sub = sub[(sub["date"] == latest) | latest.isna()]
    sub = sub.sort_values(["location_key", "is_treatment"])
    return sub.groupby("location_key").tail(1)[columns].reset_index(drop=True)


def quality_by_location(procedure_id: str, quality: pd.DataFrame | None = None) -> pd.DataFrame:
    """Quality verdict per location for the procedure (see pipeline/quality.py for the method)."""
    if quality is None:
        measurements = _read(PROCESSED / "measurements.csv")
        quality = with_catalogue(measurements, indicator_catalogue()) if not measurements.empty else measurements
    return hospital_verdict(compare(quality), procedure_id)


def policy_name(policy: dict) -> str:
    """Unique display name: label + polis."""
    return f"{policy['label']} – {policy['polis']}"


def overview(lat: float, lon: float, procedure_id: str, radius_km: float = 25, year: int = 2027,
             policies: pd.DataFrame | None = None, contracts: pd.DataFrame | None = None,
             waits: pd.DataFrame | None = None, quality: pd.DataFrame | None = None,
             hospital_table: pd.DataFrame | None = None, con=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (per-policy summary, per-policy × hospital detail). Both carry a unique `naam` column.

    Linkage: locations by location_key (organisation AGB + postcode); quality and waiting times
    per location; contracts per organisation (AGB), because hospitals contract as one organisation."""
    precomputed = None
    if con is not None and hospital_table is None and quality is None:
        from pipeline.db_queries import has_quality_data, locations_for_procedure, quality_latest
        if has_quality_data(con):  # the database already holds every comparison
            hospital_table = locations_for_procedure(con, procedure_id)
            precomputed = quality_latest(con, procedure_id).drop(columns=["procedure_id"])
    if hospital_table is None:
        measurements = _read(PROCESSED / "measurements.csv") if quality is None else quality
        hospital_table = candidate_locations(procedure_id, measurements)
    near = hospitals_within(lat, lon, radius_km, hospital_table)
    policies = load_policies(year) if policies is None else policies
    contracts = attach_organisation(load_contracts(year) if contracts is None else contracts)
    near = near.merge(latest_waits(procedure_id, waits), on="location_key", how="left")
    verdicts = precomputed if precomputed is not None else quality_by_location(procedure_id, quality)
    near = near.merge(verdicts, on="location_key", how="left")
    near["quality_verdict"] = near["quality_verdict"].fillna("geen_data")

    detail_rows = []
    for policy in policies.to_dict("records"):
        for hosp in near.to_dict("records"):
            contract = contract_for(contracts, hosp.get("organisatie_agb"), policy["concern"], policy["label"]) or {}
            detail_rows.append({
                "naam": policy_name(policy), "concern": policy["concern"], "label": policy["label"], "polis": policy["polis"],
                "location_key": hosp["location_key"],
                "location": hosp["location_name"], "distance_km": round(hosp["distance_km"], 1),
                "access": access_status(policy, contract or None),
                "contract_peildatum": contract.get("peildatum"),
                "contract_source": contract.get("source_url") or contract.get("source"),
                "wait_weeks": hosp.get("weeks"), "wait_peildatum": hosp.get("peildatum"),
                "quality": hosp["quality_verdict"], "quality_better": hosp.get("n_beter"),
                "quality_worse": hosp.get("n_slechter"), "quality_year": hosp.get("verslagjaar"),
                "volume": hosp.get("volume"),
            })
    detail = pd.DataFrame(detail_rows)
    if detail.empty:
        return pd.DataFrame(), detail

    def summarise(group: pd.DataFrame) -> pd.Series:
        access = group["access"]
        reachable = access.isin(["gecontracteerd", "gecontracteerd_met_plafond", "vrije_keuze"])
        waits_ok = group.loc[reachable, "wait_weeks"].dropna()
        quality = group.loc[reachable, "quality"]
        return pd.Series({
            # quality first: this is what the comparison is about
            "kwaliteit_boven_gemiddeld": int(quality.eq("boven_gemiddeld").sum()),
            "kwaliteit_gemengd": int(quality.eq("gemengd").sum()),
            "kwaliteit_onder_gemiddeld": int(quality.eq("onder_gemiddeld").sum()),
            "kwaliteit_geen_data": int(quality.eq("geen_data").sum()),
            # what is at stake while contract status is still unknown
            "boven_gemiddeld_contract_onbekend": int((group["quality"].eq("boven_gemiddeld") & access.eq("onbekend")).sum()),
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


INSURER_STATUSES = ["gecontracteerd", "in_onderhandeling", "geen_contract", "onbekend"]


def insurer_overview(near: pd.DataFrame, contracts: pd.DataFrame, concerns: list[str],
                     verdict_col: str = "quality_verdict") -> pd.DataFrame:
    """Per insurer (concern): how many of the better-than-average hospitals in reach it has contracted,
    is negotiating with, has no contract with, or whose status we do not know (yet).

    `near` has one row per hospital location with organisatie_agb and a verdict column. The status
    used is the concern's own label (e.g. 'VGZ') or a concern-wide row; a ceiling counts as contracted."""
    better = near[near[verdict_col] == "boven_gemiddeld"]
    rows = []
    for concern in concerns:
        counts = dict.fromkeys(INSURER_STATUSES, 0)
        for agb in better["organisatie_agb"]:
            status = (contract_for(contracts, agb, concern, concern) or {}).get("status", "onbekend") \
                if not contracts.empty else "onbekend"
            counts[status if status in counts else "onbekend"] += 1
        rows.append({"concern": concern, "betere_ziekenhuizen": len(better), **counts})
    out = pd.DataFrame(rows)
    return out.sort_values(["gecontracteerd", "in_onderhandeling", "onbekend"], ascending=[False, False, True]) \
        .reset_index(drop=True)


def policy_overview(near: pd.DataFrame, contracts: pd.DataFrame, policies: pd.DataFrame,
                    verdict_col: str = "quality_verdict") -> pd.DataFrame:
    """Per policy: of the better-than-average hospitals in reach, how many are fully reimbursed
    (contracted, or the policy pays non-contracted care in full), partly (non-contracted with a
    known lower percentage) or unknown. Sorted on fully reimbursed, then premium."""
    better = near[near[verdict_col] == "boven_gemiddeld"]
    rows = []
    for pol in policies.to_dict("records"):
        pct = pd.to_numeric(pol.get("vergoeding_niet_gecontracteerd_pct"), errors="coerce")
        full = part = unknown = 0
        for agb in better["organisatie_agb"]:
            row = (contract_for(contracts, agb, pol["concern"], pol["label"]) or {}) if not contracts.empty else {}
            status = row.get("status")
            if status == "in_onderhandeling" and row.get("origin") != "verzekeraar":
                status = None  # a hospital's 'in talks' does not say what the insurer pays meanwhile
            if status in ("gecontracteerd", "gecontracteerd_met_plafond", "vergoed_als_contract") \
                    or (pd.notna(pct) and pct >= 100):
                full += 1
            elif status in ("geen_contract", "in_onderhandeling") and pd.notna(pct):
                part += 1
            else:
                unknown += 1
        rows.append({**pol, "betere_ziekenhuizen": len(better), "volledig": full, "deels": part, "onbekend": unknown,
                     "premie": pd.to_numeric(pol.get("premie_per_maand"), errors="coerce")})
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["volledig", "premie"], ascending=[False, True], na_position="last").reset_index(drop=True)
