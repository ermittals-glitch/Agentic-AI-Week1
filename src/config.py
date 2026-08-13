"""Application-wide constants and UI copy."""

from __future__ import annotations

APP_TITLE = "Healthcare Claims Analytics Dashboard"
APP_SUBTITLE = "Understand your healthcare claims, costs, and benchmarks"

GLOBAL_DISCLAIMER_LINES = [
    "This dashboard is for learning and demonstration purposes only.",
    "Data may include synthetic sample records and CMS public reference values.",
    "This project is not affiliated with, endorsed by, or representing any organization.",
    "Information shown is not medical, legal, or billing advice.",
]

TAB_DISCLAIMER = (
    "Sample/demo data notice: values may come from synthetic records and CMS public datasets. "
    "This app is educational and not an official insurer, provider, or government tool."
)

CLAIMS_REQUIRED_COLUMNS = [
    "claim_id",
    "service_date",
    "provider_name",
    "hcpcs_code",
    "service_description",
    "service_category",
    "provider_charge",
    "allowed_amount",
    "insurance_paid",
    "deductible",
    "copay",
    "coinsurance",
    "patient_responsibility",
    "claim_status",
]

CMS_REQUIRED_COLUMNS = [
    "hcpcs_code",
    "cms_service_description",
    "place_of_service",
    "avg_submitted_charge",
    "avg_medicare_allowed_amount",
    "avg_medicare_payment",
    "benchmark_type",
    "source_url",
]

NUMERIC_CLAIM_COLUMNS = [
    "provider_charge",
    "allowed_amount",
    "insurance_paid",
    "deductible",
    "copay",
    "coinsurance",
    "patient_responsibility",
]

NUMERIC_CMS_COLUMNS = [
    "avg_submitted_charge",
    "avg_medicare_allowed_amount",
    "avg_medicare_payment",
]

FIELD_LABELS = {
    "claim_id": "Claim Number",
    "service_date": "Date of Service",
    "provider_name": "Provider",
    "hcpcs_code": "HCPCS Code",
    "service_description": "Service Description",
    "service_category": "Service Category",
    "provider_charge": "Provider Charge",
    "allowed_amount": "Allowed Amount",
    "insurance_paid": "Insurance Paid",
    "deductible": "Deductible",
    "copay": "Copay",
    "coinsurance": "Coinsurance",
    "patient_responsibility": "Patient Responsibility",
    "claim_status": "Claim Status",
}
