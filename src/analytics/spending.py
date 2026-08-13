"""Spending analysis aggregations."""

from __future__ import annotations

import pandas as pd


def by_category(claims_df: pd.DataFrame) -> pd.DataFrame:
    return (
        claims_df.groupby("service_category", as_index=False)[
            ["provider_charge", "insurance_paid", "patient_responsibility"]
        ]
        .sum()
        .sort_values("provider_charge", ascending=False)
    )


def by_provider(claims_df: pd.DataFrame) -> pd.DataFrame:
    return (
        claims_df.groupby("provider_name", as_index=False)[
            ["provider_charge", "insurance_paid", "patient_responsibility"]
        ]
        .sum()
        .sort_values("provider_charge", ascending=False)
    )


def by_month(claims_df: pd.DataFrame) -> pd.DataFrame:
    monthly = claims_df.copy()
    monthly = monthly.dropna(subset=["service_date"])
    monthly["service_month"] = monthly["service_date"].dt.to_period("M").astype(str)
    return (
        monthly.groupby("service_month", as_index=False)[
            ["provider_charge", "insurance_paid", "patient_responsibility"]
        ]
        .sum()
        .sort_values("service_month")
    )
