"""Rule-based extraction helpers for EOB text."""

from __future__ import annotations

import re
from typing import Any


def _first_match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip()


def extract_eob_fields(raw_text: str, filename: str) -> dict[str, Any]:
    text = raw_text or ""

    member = _first_match(r"Member\s+([A-Za-z\s]+)\s+Member ID", text)
    member_id = _first_match(r"Member ID\s+([A-Za-z0-9\-]+)", text)
    claim_number = _first_match(r"Claim Number\s+([A-Za-z0-9\-]+)", text)
    provider = _first_match(r"Provider\s+(.+?)\s+Date of Service", text)
    date_of_service = _first_match(r"Date of Service\s+([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})", text)
    state = _first_match(r"State\s+([A-Za-z]+)", text)

    provider_charge = _first_match(
        r"Total provider charges\s*\$([0-9,]+\.?[0-9]*)", text
    ) or _first_match(r"Provider Charge[^\$]*\$([0-9,]+\.?[0-9]*)", text)
    allowed = _first_match(
        r"Total allowed amount\s*\$([0-9,]+\.?[0-9]*)", text
    ) or _first_match(r"Allowed Amount[^\$]*\$([0-9,]+\.?[0-9]*)", text)
    insurance_paid = _first_match(
        r"Total plan payment\s*\$([0-9,]+\.?[0-9]*)", text
    ) or _first_match(r"Insurance Paid[^\$]*\$([0-9,]+\.?[0-9]*)", text)
    patient_resp = _first_match(
        r"Patient(?:/other)? responsibility\*?\s*\$([0-9,]+\.?[0-9]*)", text
    ) or _first_match(r"You Owe[^\$]*\$([0-9,]+\.?[0-9]*)", text)

    hcpcs_matches = re.findall(r"\b(\d{5})\b", text)
    hcpcs_codes = sorted(set(hcpcs_matches))

    return {
        "source_file": filename,
        "member_name": member,
        "member_id": member_id,
        "claim_number": claim_number,
        "provider": provider,
        "date_of_service": date_of_service,
        "state": state,
        "provider_charge_text": provider_charge,
        "allowed_amount_text": allowed,
        "insurance_paid_text": insurance_paid,
        "patient_responsibility_text": patient_resp,
        "detected_hcpcs_codes": ", ".join(hcpcs_codes),
        "raw_text": text,
    }
