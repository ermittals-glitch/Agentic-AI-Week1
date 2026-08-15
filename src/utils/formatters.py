"""Formatting helpers for UI display."""

from __future__ import annotations

import pandas as pd


def to_currency(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "$0.00"
    return f"${float(value):,.2f}"


def to_currency_or_na(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "Not available"
    return f"${float(value):,.2f}"


def to_percent(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "0.0%"
    return f"{float(value):.1f}%"


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)
