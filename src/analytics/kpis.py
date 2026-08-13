"""Top-level KPI calculations for claims overview."""

from __future__ import annotations

import pandas as pd


def build_claim_kpis(claims_df: pd.DataFrame) -> dict[str, float | int]:
    return {
        "claim_count": int(claims_df["claim_id"].nunique()),
        "service_lines": int(len(claims_df)),
        "total_provider_charge": float(claims_df["provider_charge"].sum()),
        "total_allowed": float(claims_df["allowed_amount"].sum()),
        "total_insurance_paid": float(claims_df["insurance_paid"].sum()),
        "total_patient_responsibility": float(claims_df["patient_responsibility"].sum()),
    }
