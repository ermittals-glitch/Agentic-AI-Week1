"""Text and glossary helpers for member-friendly explanations."""

from __future__ import annotations

GLOSSARY = {
    "Provider Charge": "The amount the provider billed for the service.",
    "Allowed Amount": "The amount your health plan recognizes for payment after plan rules/contract rates.",
    "Insurance Paid": "The portion paid by your health plan.",
    "Deductible": "Amount you pay before many plan benefits start sharing costs.",
    "Copay": "A fixed dollar amount you pay for certain services.",
    "Coinsurance": "A percentage of cost you pay after allowed amount is applied.",
    "Patient Responsibility": "What remains for the member/patient or other payer after plan payment.",
}


def build_disclaimer_block(lines: list[str]) -> str:
    return "\n".join([f"- {line}" for line in lines])
