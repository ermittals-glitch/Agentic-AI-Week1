"""Load uploaded files and normalize into app dataframes."""

from __future__ import annotations

from io import BytesIO
from typing import Literal

import pandas as pd

from src.config import CLAIMS_REQUIRED_COLUMNS
from src.data.schema import (
    coerce_claim_types,
    coerce_cms_types,
    normalize_column_names,
)
from src.data.validators import validate_claims_dataframe, validate_cms_dataframe


class DataLoadError(Exception):
    """Raised when uploaded data cannot be loaded safely."""


def load_default_cms_reference() -> pd.DataFrame:
    """Built-in CMS reference data used when member upload does not include CMS sheet."""
    rows = [
        {
            "hcpcs_code": "99213",
            "cms_service_description": "Established patient office/outpatient visit, low-level decision making",
            "place_of_service": "Office",
            "avg_submitted_charge": 148.0,
            "avg_medicare_allowed_amount": 85.0,
            "avg_medicare_payment": 60.0,
            "benchmark_type": "CMS provider-level public example",
            "source_url": "https://data.cms.gov/tools/medicare-physician-other-practitioner-look-up-tool/provider/1831544154",
        },
        {
            "hcpcs_code": "36415",
            "cms_service_description": "Insertion of needle into vein for collection of blood sample",
            "place_of_service": "Office",
            "avg_submitted_charge": 19.0,
            "avg_medicare_allowed_amount": 9.0,
            "avg_medicare_payment": 9.0,
            "benchmark_type": "CMS provider-level public example",
            "source_url": "https://data.cms.gov/tools/medicare-physician-other-practitioner-look-up-tool/provider/1154379907",
        },
        {
            "hcpcs_code": "80053",
            "cms_service_description": "Blood test, comprehensive group of blood chemicals",
            "place_of_service": "Office",
            "avg_submitted_charge": 55.0,
            "avg_medicare_allowed_amount": 10.0,
            "avg_medicare_payment": 10.0,
            "benchmark_type": "CMS provider-level public example",
            "source_url": "https://data.cms.gov/tools/medicare-physician-other-practitioner-look-up-tool/provider/1154379907",
        },
        {
            "hcpcs_code": "80061",
            "cms_service_description": "Blood test, lipids (cholesterol and triglycerides)",
            "place_of_service": "Office",
            "avg_submitted_charge": 51.0,
            "avg_medicare_allowed_amount": 13.0,
            "avg_medicare_payment": 13.0,
            "benchmark_type": "CMS provider-level public example",
            "source_url": "https://data.cms.gov/tools/medicare-physician-other-practitioner-look-up-tool/provider/1154379907",
        },
        {
            "hcpcs_code": "99284",
            "cms_service_description": "Emergency department visit with moderate level of medical decision making",
            "place_of_service": "Facility",
            "avg_submitted_charge": 388.0,
            "avg_medicare_allowed_amount": 116.0,
            "avg_medicare_payment": 90.0,
            "benchmark_type": "CMS provider-level public example",
            "source_url": "https://data.cms.gov/tools/medicare-physician-other-practitioner-look-up-tool/provider/1982090932",
        },
        {
            "hcpcs_code": "99285",
            "cms_service_description": "Emergency department visit with high level of medical decision making",
            "place_of_service": "Facility",
            "avg_submitted_charge": 624.0,
            "avg_medicare_allowed_amount": 187.0,
            "avg_medicare_payment": 145.0,
            "benchmark_type": "CMS provider-level public example",
            "source_url": "https://data.cms.gov/tools/medicare-physician-other-practitioner-look-up-tool/provider/1255519922",
        },
        {
            "hcpcs_code": "99222",
            "cms_service_description": "Initial hospital care, at least 55 minutes if time-based",
            "place_of_service": "Facility",
            "avg_submitted_charge": 808.0,
            "avg_medicare_allowed_amount": 143.0,
            "avg_medicare_payment": 114.0,
            "benchmark_type": "CMS provider-level public example",
            "source_url": "https://data.cms.gov/tools/medicare-physician-other-practitioner-look-up-tool/provider/1497076400",
        },
        {
            "hcpcs_code": "99223",
            "cms_service_description": "Initial hospital care, at least 75 minutes if time-based",
            "place_of_service": "Facility",
            "avg_submitted_charge": 1282.0,
            "avg_medicare_allowed_amount": 190.0,
            "avg_medicare_payment": 151.0,
            "benchmark_type": "CMS provider-level public example",
            "source_url": "https://data.cms.gov/tools/medicare-physician-other-practitioner-look-up-tool/provider/1497076400",
        },
    ]
    return coerce_cms_types(pd.DataFrame(rows))


def _pick_sheet_name(sheet_names: list[str], candidates: list[str]) -> str | None:
    lower_map = {s.lower(): s for s in sheet_names}
    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]
    return None


def _find_claims_sheet_by_schema(xls: pd.ExcelFile) -> str | None:
    required = set(CLAIMS_REQUIRED_COLUMNS)
    for sheet in xls.sheet_names:
        try:
            probe = pd.read_excel(xls, sheet_name=sheet, nrows=1)
        except Exception:
            continue
        normalized_cols = {str(c).strip().lower() for c in probe.columns}
        if required.issubset(normalized_cols):
            return sheet
    return None


def load_claims_excel(
    file_bytes: bytes,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Literal["uploaded", "built_in"]]:
    """Return member_info, claims_df, cms_df, cms_source from uploaded workbook bytes."""
    stream = BytesIO(file_bytes)

    try:
        xls = pd.ExcelFile(stream, engine="openpyxl")
    except Exception as exc:
        raise DataLoadError(f"Could not open Excel file: {exc}") from exc

    claims_sheet = _pick_sheet_name(xls.sheet_names, ["Claims"])
    if not claims_sheet:
        claims_sheet = _find_claims_sheet_by_schema(xls)
    cms_sheet = _pick_sheet_name(xls.sheet_names, ["CMS_Reference_Data", "CMS Reference Data"])
    member_sheet = _pick_sheet_name(xls.sheet_names, ["Member_Info", "Member Info"])

    if not claims_sheet:
        raise DataLoadError(
            "Could not find a claims sheet. Provide a sheet named 'Claims' or a sheet with required claim columns."
        )

    member_df = pd.DataFrame()
    if member_sheet:
        member_df = pd.read_excel(xls, sheet_name=member_sheet)
        member_df = normalize_column_names(member_df)

    claims_df = pd.read_excel(xls, sheet_name=claims_sheet)
    cms_source: Literal["uploaded", "built_in"] = "uploaded"
    if cms_sheet:
        cms_df = pd.read_excel(xls, sheet_name=cms_sheet)
        cms_df = normalize_column_names(cms_df)
        cms_df = coerce_cms_types(cms_df)
        cms_ok, cms_issues = validate_cms_dataframe(cms_df)
        if not cms_ok:
            raise DataLoadError("; ".join(cms_issues))
    else:
        cms_df = load_default_cms_reference()
        cms_source = "built_in"

    claims_df = normalize_column_names(claims_df)
    claims_df = coerce_claim_types(claims_df)

    claims_ok, claim_issues = validate_claims_dataframe(claims_df)

    if not claims_ok:
        raise DataLoadError("; ".join(claim_issues))

    return member_df, claims_df, cms_df, cms_source
