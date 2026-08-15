"""Text and glossary helpers for member-friendly explanations."""

from __future__ import annotations

GLOSSARY = {
    "Amount the provider billed": "The provider's original charge before insurance discounts.",
    "Plan's negotiated amount": (
        "The amount your plan recognizes for this service. For in-network care, you generally do not owe the "
        "difference between the original charge and this negotiated amount."
    ),
    "What insurance paid": "The portion paid by your health plan toward the negotiated amount.",
    "Deductible": "The amount you pay before your plan starts sharing many costs. It usually resets each plan year.",
    "Copay": "A fixed amount you pay for a visit or service, such as $25 for an office visit.",
    "Coinsurance": "Your percentage of the negotiated amount after applicable deductible rules.",
    "What you may owe": (
        "The amount assigned to you or another payer on the claim. Secondary insurance or payments already made "
        "may change the final provider bill."
    ),
    "Insurance service code": (
        "A code insurers use to identify a medical service. It is mainly useful when asking your insurer about a claim."
    ),
}


def build_disclaimer_block(lines: list[str]) -> str:
    return "\n".join([f"- {line}" for line in lines])
