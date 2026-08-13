"""Schema and coercion logic for claims and CMS reference data."""

from __future__ import annotations

import pandas as pd

from src.config import (
    CLAIMS_REQUIRED_COLUMNS,
    CMS_REQUIRED_COLUMNS,
    NUMERIC_CLAIM_COLUMNS,
    NUMERIC_CMS_COLUMNS,
)


def missing_columns(df: pd.DataFrame, required_columns: list[str]) -> list[str]:
    present = set(df.columns.str.strip())
    return [col for col in required_columns if col not in present]


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]
    return out


def coerce_claim_types(claims_df: pd.DataFrame) -> pd.DataFrame:
    df = claims_df.copy()
    df["service_date"] = pd.to_datetime(df["service_date"], errors="coerce")
    for col in NUMERIC_CLAIM_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    text_cols = [
        "claim_id",
        "provider_name",
        "hcpcs_code",
        "service_description",
        "service_category",
        "claim_status",
    ]
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()
    return df


def coerce_cms_types(cms_df: pd.DataFrame) -> pd.DataFrame:
    df = cms_df.copy()
    for col in NUMERIC_CMS_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    text_cols = [
        "hcpcs_code",
        "cms_service_description",
        "place_of_service",
        "benchmark_type",
        "source_url",
    ]
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()
    return df


def claims_contract_columns() -> list[str]:
    return CLAIMS_REQUIRED_COLUMNS.copy()


def cms_contract_columns() -> list[str]:
    return CMS_REQUIRED_COLUMNS.copy()
