"""Plain-English claim explanation logic."""

from __future__ import annotations

import pandas as pd

from src.utils.formatters import to_currency


def _optional_float(value: object) -> float:
    return float("nan") if value is None or pd.isna(value) else float(value)


def explain_claim_line(claim_row: pd.Series) -> str:
    provider_charge = float(claim_row["provider_charge"])
    allowed = float(claim_row["allowed_amount"])
    insurance_paid = float(claim_row["insurance_paid"])
    deductible = _optional_float(claim_row["deductible"])
    copay = _optional_float(claim_row["copay"])
    coinsurance = _optional_float(claim_row["coinsurance"])
    patient_resp = float(claim_row["patient_responsibility"])
    negotiated_difference = max(0.0, provider_charge - allowed)
    responsibility_label = str(claim_row.get("responsibility_label", "You may owe"))

    explanation = (
        f"The provider billed {to_currency(provider_charge)} for {claim_row['service_description']}. "
        f"Your plan's negotiated amount was {to_currency(allowed)}. The {to_currency(negotiated_difference)} difference "
        "commonly reflects a plan discount for in-network care; check your EOB before assuming you owe it. "
        f"Your insurance paid {to_currency(insurance_paid)}. "
    )

    if "other" in responsibility_label.lower():
        explanation += (
            f"The EOB shows {to_currency(patient_resp)} as patient/other responsibility. This may include another payer "
            "and should not be treated as your final bill."
        )
    else:
        explanation += (
            f"The claim shows {to_currency(patient_resp)} that you may owe. A provider bill, secondary insurance, "
            "or payments already made may change the final amount."
        )

    known_cost_share = {
        "deductible": deductible,
        "copay": copay,
        "coinsurance": coinsurance,
    }
    known_parts = [
        value
        for value in known_cost_share.values()
        if not pd.isna(value)
    ]
    nonzero_parts = [
        f"{name} {to_currency(value)}"
        for name, value in known_cost_share.items()
        if not pd.isna(value) and value > 0
    ]
    if nonzero_parts:
        explanation += " The available cost-share breakdown is " + ", ".join(nonzero_parts) + "."
    elif known_parts and patient_resp == 0:
        explanation += " No deductible, copay, or coinsurance was shown for this service."
    elif known_parts:
        explanation += " The available cost-share fields do not fully explain the remaining amount. Ask your insurer for details."
    else:
        explanation += " This EOB did not provide a reliable deductible, copay, and coinsurance breakdown."

    return explanation


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
