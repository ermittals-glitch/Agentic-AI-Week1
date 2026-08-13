"""Adapt parsed EOB records into a claim-like dataframe for member-facing analytics tabs."""

from __future__ import annotations

import pandas as pd

from src.config import CLAIMS_REQUIRED_COLUMNS


def _to_float(value: object) -> float:
    if value is None or pd.isna(value):
        return 0.0
    cleaned = str(value).replace("$", "").replace(",", "").strip()
    if not cleaned:
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def build_eob_claims_view(parsed_eob_df: pd.DataFrame | None) -> pd.DataFrame:
    if parsed_eob_df is None or parsed_eob_df.empty:
        return pd.DataFrame(columns=CLAIMS_REQUIRED_COLUMNS)

    eob = parsed_eob_df.copy().reset_index(drop=True)

    out = pd.DataFrame()
    out["claim_id"] = eob["claim_number"].fillna("").astype(str).str.strip()
    out.loc[out["claim_id"] == "", "claim_id"] = [f"EOB-{i+1:03d}" for i in out.index]

    out["service_date"] = pd.to_datetime(eob.get("date_of_service"), errors="coerce")
    out["provider_name"] = eob.get("provider", "Unknown Provider").fillna("Unknown Provider").astype(str)
    out["hcpcs_code"] = eob.get("detected_hcpcs_codes", "").fillna("").astype(str)
    out["service_description"] = "Parsed EOB claim summary"
    out["service_category"] = "EOB Claim"

    out["provider_charge"] = eob.get("provider_charge_text", 0).apply(_to_float)
    out["allowed_amount"] = eob.get("allowed_amount_text", 0).apply(_to_float)
    out["insurance_paid"] = eob.get("insurance_paid_text", 0).apply(_to_float)

    # EOB parsing currently captures total patient responsibility but may not
    # include line-level deductible/copay/coinsurance for every file format.
    out["deductible"] = 0.0
    out["copay"] = 0.0
    out["coinsurance"] = 0.0
    out["patient_responsibility"] = eob.get("patient_responsibility_text", 0).apply(_to_float)
    out["claim_status"] = eob.get("parse_status", "Parsed").fillna("Parsed").astype(str)

    return out[CLAIMS_REQUIRED_COLUMNS]
