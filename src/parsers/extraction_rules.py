"""Rule-based extraction helpers for EOB text."""

from __future__ import annotations

import re
from typing import Any


MONEY_PATTERN = r"\$([0-9,]+(?:\.[0-9]{2})?)"
SERVICE_LINE_PATTERN = re.compile(
    rf"^\s*(\d{{5}})\s+(.+?)\s+{MONEY_PATTERN}\s+{MONEY_PATTERN}\s+{MONEY_PATTERN}\s+{MONEY_PATTERN}\s*$",
    re.IGNORECASE,
)


def _first_match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip()


def _amount_from_label(label_pattern: str, lines: list[str]) -> str | None:
    pattern = re.compile(rf"^\s*{label_pattern}\s+{MONEY_PATTERN}\s*$", re.IGNORECASE)
    for line in lines:
        match = pattern.match(line)
        if match:
            return match.group(1)
    return None


def _parse_service_lines(lines: list[str]) -> list[dict[str, str]]:
    services: list[dict[str, str]] = []
    for line in lines:
        match = SERVICE_LINE_PATTERN.match(line)
        if not match:
            continue
        services.append(
            {
                "hcpcs_code": match.group(1),
                "service_description": match.group(2).strip(),
                "provider_charge_text": match.group(3),
                "allowed_amount_text": match.group(4),
                "insurance_paid_text": match.group(5),
                "patient_responsibility_text": match.group(6),
            }
        )
    return services


def _sum_service_amount(service_lines: list[dict[str, str]], field: str) -> str | None:
    if not service_lines:
        return None
    total = sum(float(row[field].replace(",", "")) for row in service_lines)
    return f"{total:.2f}"


def _validate_financials(
    allowed_text: str | None,
    insurance_paid_text: str | None,
    responsibility_text: str | None,
) -> list[str]:
    if not all([allowed_text, insurance_paid_text, responsibility_text]):
        return ["Some financial amounts could not be extracted from this EOB."]

    allowed = float(allowed_text.replace(",", ""))
    insurance_paid = float(insurance_paid_text.replace(",", ""))
    responsibility = float(responsibility_text.replace(",", ""))
    if abs(allowed - insurance_paid - responsibility) > 0.02:
        return ["Extracted amounts do not reconcile to the allowed amount."]
    return []


def extract_eob_fields(raw_text: str, filename: str) -> dict[str, Any]:
    text = raw_text or ""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    service_lines = _parse_service_lines(lines)

    member = _first_match(r"Member\s+([A-Za-z\s]+)\s+Member ID", text)
    member_id = _first_match(r"Member ID\s+([A-Za-z0-9\-]+)", text)
    claim_number = _first_match(r"Claim Number\s+([A-Za-z0-9\-]+)", text)
    provider = _first_match(r"^Provider\s+(.+?)\s+(?:Date of Service|State)\s+", text)
    date_of_service = _first_match(r"Date of Service\s+([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})", text)
    state = _first_match(r"(?:^|\s)State\s+([A-Za-z]+)(?:\s|$)", text)

    provider_charge = _amount_from_label(r"Total provider charges", lines) or _sum_service_amount(
        service_lines, "provider_charge_text"
    )
    allowed = _amount_from_label(r"Total allowed amount", lines) or _sum_service_amount(
        service_lines, "allowed_amount_text"
    )
    insurance_paid = _amount_from_label(r"Total plan payment", lines) or _sum_service_amount(
        service_lines, "insurance_paid_text"
    )
    patient_resp = _amount_from_label(r"Patient(?:/other)? responsibility\*?", lines) or _sum_service_amount(
        service_lines, "patient_responsibility_text"
    )

    deductible = _amount_from_label(r"Deductible", lines)
    copay = _amount_from_label(r"Copay", lines)
    coinsurance = _amount_from_label(r"Coinsurance", lines)
    validation_messages = _validate_financials(allowed, insurance_paid, patient_resp)
    hcpcs_codes = [row["hcpcs_code"] for row in service_lines]

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
        "deductible_text": deductible,
        "copay_text": copay,
        "coinsurance_text": coinsurance,
        "detected_hcpcs_codes": ", ".join(hcpcs_codes),
        "service_lines": service_lines,
        "extraction_confidence": "Needs review" if validation_messages or not service_lines else "Validated",
        "validation_messages": validation_messages,
        "responsibility_label": (
            "Patient/other responsibility" if re.search(r"Patient/other responsibility", text, re.IGNORECASE) else "You may owe"
        ),
        "raw_text": text,
    }
