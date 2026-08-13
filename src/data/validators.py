"""Validation rules and quality checks."""

from __future__ import annotations

import pandas as pd

from src.config import CLAIMS_REQUIRED_COLUMNS, CMS_REQUIRED_COLUMNS
from src.data.schema import missing_columns


def validate_claims_dataframe(df: pd.DataFrame) -> tuple[bool, list[str]]:
    issues: list[str] = []
    missing = missing_columns(df, CLAIMS_REQUIRED_COLUMNS)
    if missing:
        issues.append(f"Missing required claims columns: {', '.join(missing)}")

    if "claim_id" in df.columns and df["claim_id"].isna().any():
        issues.append("Claims file has blank claim_id values.")

    if "service_date" in df.columns and df["service_date"].isna().all():
        issues.append("All service_date values appear invalid or missing.")

    return len(issues) == 0, issues


def validate_cms_dataframe(df: pd.DataFrame) -> tuple[bool, list[str]]:
    issues: list[str] = []
    missing = missing_columns(df, CMS_REQUIRED_COLUMNS)
    if missing:
        issues.append(f"Missing required CMS columns: {', '.join(missing)}")

    if "hcpcs_code" in df.columns and df["hcpcs_code"].isna().any():
        issues.append("CMS data has blank hcpcs_code values.")

    return len(issues) == 0, issues


def build_quality_report(claims_df: pd.DataFrame | None, cms_df: pd.DataFrame | None) -> dict:
    report = {
        "claims_rows": 0,
        "cms_rows": 0,
        "claims_missing_dates": 0,
        "claims_missing_hcpcs": 0,
        "claims_zero_allowed": 0,
    }

    if claims_df is not None and not claims_df.empty:
        report["claims_rows"] = len(claims_df)
        report["claims_missing_dates"] = int(claims_df["service_date"].isna().sum())
        report["claims_missing_hcpcs"] = int((claims_df["hcpcs_code"].astype(str).str.strip() == "").sum())
        report["claims_zero_allowed"] = int((claims_df["allowed_amount"] <= 0).sum())

    if cms_df is not None and not cms_df.empty:
        report["cms_rows"] = len(cms_df)

    return report
