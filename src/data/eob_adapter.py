"""Adapt parsed EOB records into a claim-like dataframe for member-facing analytics tabs."""

from __future__ import annotations

import pandas as pd

from src.config import CLAIMS_REQUIRED_COLUMNS


def _to_float(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    cleaned = str(value).replace("$", "").replace(",", "").strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _service_category(description: str) -> str:
    normalized = description.lower()
    if "emergency" in normalized:
        return "Emergency care"
    if any(term in normalized for term in ["blood", "panel", "laboratory"]):
        return "Lab tests"
    if any(term in normalized for term in ["eye", "visual", "cornea", "optic"]):
        return "Vision care"
    if "hospital" in normalized:
        return "Hospital care"
    if "visit" in normalized or "office" in normalized:
        return "Office visit"
    return "Other care"


def build_eob_claims_view(parsed_eob_df: pd.DataFrame | None) -> pd.DataFrame:
    if parsed_eob_df is None or parsed_eob_df.empty:
        return pd.DataFrame(columns=CLAIMS_REQUIRED_COLUMNS)

    rows: list[dict] = []
    for eob_index, record in parsed_eob_df.reset_index(drop=True).iterrows():
        claim_id = str(record.get("claim_number") or "").strip() or f"EOB-{eob_index + 1:03d}"
        service_lines = record.get("service_lines")
        if not isinstance(service_lines, list) or not service_lines:
            service_lines = [
                {
                    "hcpcs_code": str(record.get("detected_hcpcs_codes") or ""),
                    "service_description": "Claim summary from uploaded EOB",
                    "provider_charge_text": record.get("provider_charge_text"),
                    "allowed_amount_text": record.get("allowed_amount_text"),
                    "insurance_paid_text": record.get("insurance_paid_text"),
                    "patient_responsibility_text": record.get("patient_responsibility_text"),
                }
            ]

        single_service = len(service_lines) == 1
        for service in service_lines:
            description = str(service.get("service_description") or "Service from uploaded EOB")
            rows.append(
                {
                    "claim_id": claim_id,
                    "service_date": pd.to_datetime(record.get("date_of_service"), errors="coerce"),
                    "provider_name": str(record.get("provider") or "Provider not identified"),
                    "hcpcs_code": str(service.get("hcpcs_code") or ""),
                    "service_description": description,
                    "service_category": _service_category(description),
                    "provider_charge": _to_float(service.get("provider_charge_text")),
                    "allowed_amount": _to_float(service.get("allowed_amount_text")),
                    "insurance_paid": _to_float(service.get("insurance_paid_text")),
                    "deductible": _to_float(record.get("deductible_text")) if single_service else None,
                    "copay": _to_float(record.get("copay_text")) if single_service else None,
                    "coinsurance": _to_float(record.get("coinsurance_text")) if single_service else None,
                    "patient_responsibility": _to_float(service.get("patient_responsibility_text")),
                    "claim_status": str(record.get("extraction_confidence") or "Needs review"),
                    "responsibility_label": str(record.get("responsibility_label") or "You may owe"),
                    "source_file": str(record.get("source_file") or "Uploaded EOB"),
                }
            )

    return pd.DataFrame(rows)
