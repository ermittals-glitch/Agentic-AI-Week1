from __future__ import annotations

import pandas as pd

from src.analytics.benchmark import build_claims_benchmark_analysis, build_eob_benchmark_analysis
from src.analytics.explainer import explain_claim_line
from src.data.eob_adapter import build_eob_claims_view
from src.data.loaders import load_default_cms_reference
from src.parsers.extraction_rules import extract_eob_fields


SINGLE_SERVICE_EOB = """
DEMO HEALTH PLAN
Member Jordan Taylor Member ID DEMO-784512
Plan DemoChoice PPO Group GRP-26001
State Texas Claim Number CLM-1001
Provider North Texas Family Clinic Date of Service 01/12/2026
HCPCS Service Provider Charge Allowed Amount Insurance Paid You Owe
99213 Established patient office/outpatient visit $180.00 $85.00 $68.00 $17.00
Deductible $0.00
Copay $17.00
Coinsurance $0.00
Patient Responsibility $17.00
"""

MULTI_SERVICE_EOB = """
DEMO HEALTH PLAN
Member Jordan Taylor Member ID DEMO-784512
Plan Demo Medicare-style Plan Claim Number VIS-2026-001
Date of Service 08/05/2026 Place of Service Office
Provider Demo Ophthalmology Center State Texas
HCPCS Service Provider charge Allowed Plan paid Patient/other responsibility*
92004 New patient complete exam of visual system $155.00 $140.00 $84.00 $56.00
92020 Exam of internal drainage system of eye $26.00 $26.00 $20.00 $6.00
Total provider charges $181.00
Total allowed amount $166.00
Total plan payment $104.00
Patient/other responsibility* $62.00
"""


def test_single_service_eob_extracts_reconciled_amounts_and_only_service_code() -> None:
    parsed = extract_eob_fields(SINGLE_SERVICE_EOB, "office.pdf")

    assert parsed["provider_charge_text"] == "180.00"
    assert parsed["allowed_amount_text"] == "85.00"
    assert parsed["insurance_paid_text"] == "68.00"
    assert parsed["patient_responsibility_text"] == "17.00"
    assert parsed["detected_hcpcs_codes"] == "99213"
    assert parsed["copay_text"] == "17.00"
    assert parsed["extraction_confidence"] == "Validated"

    explanation = explain_claim_line(build_eob_claims_view(pd.DataFrame([parsed])).iloc[0])
    assert "copay $17.00" in explanation
    assert "deductible $0.00" not in explanation
    assert "coinsurance $0.00" not in explanation


def test_multi_service_eob_builds_service_rows_and_preserves_unknown_cost_share() -> None:
    parsed = extract_eob_fields(MULTI_SERVICE_EOB, "vision.pdf")
    claims = build_eob_claims_view(pd.DataFrame([parsed]))

    assert claims["hcpcs_code"].tolist() == ["92004", "92020"]
    assert claims["provider_name"].unique().tolist() == ["Demo Ophthalmology Center"]
    assert claims["allowed_amount"].tolist() == [140.0, 26.0]
    assert claims["insurance_paid"].tolist() == [84.0, 20.0]
    assert claims["patient_responsibility"].tolist() == [56.0, 6.0]
    assert claims["deductible"].isna().all()
    assert claims["copay"].isna().all()
    assert claims["coinsurance"].isna().all()
    assert claims["responsibility_label"].unique().tolist() == ["Patient/other responsibility"]

    benchmark = build_eob_benchmark_analysis(pd.DataFrame([parsed]), load_default_cms_reference())
    allowed_rows = benchmark[benchmark["metric"] == "Allowed Amount"]
    assert allowed_rows["member_value"].tolist() == [140.0, 26.0]
    assert allowed_rows["service_description"].tolist() == [
        "New patient complete exam of visual system",
        "Exam of internal drainage system of eye",
    ]

    explanation = explain_claim_line(claims.iloc[0])
    assert "did not provide a reliable deductible" in explanation
    assert "patient/other responsibility" in explanation
    assert "deductible $0.00" not in explanation


def test_medicare_comparison_uses_neutral_directional_language() -> None:
    claim = pd.DataFrame(
        [
            {
                "claim_id": "A",
                "service_date": pd.Timestamp("2026-01-01"),
                "provider_name": "Provider",
                "hcpcs_code": "99213",
                "service_description": "Office visit",
                "service_category": "Office visit",
                "provider_charge": 180.0,
                "allowed_amount": 100.0,
                "insurance_paid": 80.0,
                "deductible": 0.0,
                "copay": 20.0,
                "coinsurance": 0.0,
                "patient_responsibility": 20.0,
                "claim_status": "Processed",
            }
        ]
    )

    result = build_claims_benchmark_analysis(claim, load_default_cms_reference())
    allowed_result = result[result["metric"] == "Allowed Amount"].iloc[0]
    assert allowed_result["benchmark_signal"] == "Higher than Medicare average"
