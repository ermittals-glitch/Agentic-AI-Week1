"""Plain-English claim explanation logic."""

from __future__ import annotations

import pandas as pd

from src.utils.formatters import to_currency


def explain_claim_line(claim_row: pd.Series) -> str:
    provider_charge = float(claim_row["provider_charge"])
    allowed = float(claim_row["allowed_amount"])
    insurance_paid = float(claim_row["insurance_paid"])
    deductible = float(claim_row["deductible"])
    copay = float(claim_row["copay"])
    coinsurance = float(claim_row["coinsurance"])
    patient_resp = float(claim_row["patient_responsibility"])

    return (
        f"For claim {claim_row['claim_id']} ({claim_row['service_description']}), the provider billed "
        f"{to_currency(provider_charge)}. Your plan recognized {to_currency(allowed)} as the allowed amount "
        f"and paid {to_currency(insurance_paid)}. The remaining member responsibility is {to_currency(patient_resp)}, "
        f"made up of deductible {to_currency(deductible)}, copay {to_currency(copay)}, and coinsurance {to_currency(coinsurance)}."
    )


def explain_cost_share(claim_row: pd.Series) -> pd.DataFrame:
    rows = [
        ("Provider billed", float(claim_row["provider_charge"])),
        ("Allowed by plan", float(claim_row["allowed_amount"])),
        ("Paid by plan", float(claim_row["insurance_paid"])),
        ("Deductible", float(claim_row["deductible"])),
        ("Copay", float(claim_row["copay"])),
        ("Coinsurance", float(claim_row["coinsurance"])),
        ("Patient responsibility", float(claim_row["patient_responsibility"])),
    ]
    return pd.DataFrame(rows, columns=["Item", "Amount"])
