"""Comparison logic between member claim costs and CMS reference values."""

from __future__ import annotations

import pandas as pd

from src.utils.formatters import safe_divide


def compare_claim_to_cms(claim_row: pd.Series, cms_row: pd.Series) -> pd.DataFrame:
    rows = []

    comparisons = [
        (
            "Provider Charge",
            float(claim_row["provider_charge"]),
            float(cms_row["avg_submitted_charge"]),
        ),
        (
            "Allowed Amount",
            float(claim_row["allowed_amount"]),
            float(cms_row["avg_medicare_allowed_amount"]),
        ),
        (
            "Insurance Paid",
            float(claim_row["insurance_paid"]),
            float(cms_row["avg_medicare_payment"]),
        ),
    ]

    for metric, member_value, cms_value in comparisons:
        diff = member_value - cms_value
        pct_diff = safe_divide(diff, cms_value) * 100
        if pct_diff > 10:
            flag = "Above benchmark"
        elif pct_diff < -10:
            flag = "Below benchmark"
        else:
            flag = "Near benchmark"

        rows.append(
            {
                "Metric": metric,
                "Member Value": member_value,
                "CMS Benchmark": cms_value,
                "Difference": diff,
                "Difference %": pct_diff,
                "Benchmark Signal": flag,
            }
        )

    return pd.DataFrame(rows)


def build_benchmark_join(claims_df: pd.DataFrame, cms_df: pd.DataFrame) -> pd.DataFrame:
    return claims_df.merge(cms_df, on="hcpcs_code", how="left", suffixes=("_claim", "_cms"))


def _signal_from_pct(pct_diff: float | None) -> str:
    if pct_diff is None or pd.isna(pct_diff):
        return "No CMS match"
    if pct_diff > 10:
        return "Above benchmark"
    if pct_diff < -10:
        return "Below benchmark"
    return "Near benchmark"


def _parse_amount(text_value: object) -> float | None:
    if text_value is None or pd.isna(text_value):
        return None
    cleaned = str(text_value).replace("$", "").replace(",", "").strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _extract_codes(code_blob: object) -> list[str]:
    if code_blob is None or pd.isna(code_blob):
        return []
    return [c.strip() for c in str(code_blob).split(",") if c.strip()]


def build_claims_benchmark_analysis(claims_df: pd.DataFrame, cms_df: pd.DataFrame) -> pd.DataFrame:
    claims = claims_df.copy()
    cms = cms_df.copy()

    claims["hcpcs_code"] = claims["hcpcs_code"].astype(str).str.strip()
    cms["hcpcs_code"] = cms["hcpcs_code"].astype(str).str.strip()

    merged = claims.merge(cms, on="hcpcs_code", how="left", suffixes=("_claim", "_cms"))

    rows: list[dict] = []
    for _, r in merged.iterrows():
        metrics = [
            ("Provider Charge", float(r["provider_charge"]), r.get("avg_submitted_charge")),
            ("Allowed Amount", float(r["allowed_amount"]), r.get("avg_medicare_allowed_amount")),
            ("Insurance Paid", float(r["insurance_paid"]), r.get("avg_medicare_payment")),
        ]

        for metric_name, member_value, cms_value_raw in metrics:
            cms_value = None if pd.isna(cms_value_raw) else float(cms_value_raw)
            if cms_value is None:
                diff = None
                pct_diff = None
            else:
                diff = member_value - cms_value
                pct_diff = safe_divide(diff, cms_value) * 100

            rows.append(
                {
                    "source_type": "Claims Workbook",
                    "source_file": "Uploaded claims workbook",
                    "claim_id": r.get("claim_id"),
                    "service_date": r.get("service_date"),
                    "provider_name": r.get("provider_name"),
                    "hcpcs_code": r.get("hcpcs_code"),
                    "service_description": r.get("service_description"),
                    "metric": metric_name,
                    "member_value": member_value,
                    "cms_benchmark": cms_value,
                    "difference": diff,
                    "difference_pct": pct_diff,
                    "benchmark_signal": _signal_from_pct(pct_diff),
                    "cms_service_description": r.get("cms_service_description"),
                    "place_of_service": r.get("place_of_service"),
                    "benchmark_type": r.get("benchmark_type"),
                    "source_url": r.get("source_url"),
                    "analysis_note": "",
                }
            )

    return pd.DataFrame(rows)


def build_eob_benchmark_analysis(parsed_eob_df: pd.DataFrame, cms_df: pd.DataFrame) -> pd.DataFrame:
    eob = parsed_eob_df.copy()
    cms = cms_df.copy()
    cms["hcpcs_code"] = cms["hcpcs_code"].astype(str).str.strip()

    rows: list[dict] = []
    for _, r in eob.iterrows():
        codes = _extract_codes(r.get("detected_hcpcs_codes"))
        single_code = len(codes) == 1

        provider_charge = _parse_amount(r.get("provider_charge_text"))
        allowed_amount = _parse_amount(r.get("allowed_amount_text"))
        insurance_paid = _parse_amount(r.get("insurance_paid_text"))

        for code in codes:
            cms_matches = cms[cms["hcpcs_code"] == code]
            cms_row = None if cms_matches.empty else cms_matches.iloc[0]
            metrics = [
                ("Provider Charge", provider_charge if single_code else None, "avg_submitted_charge"),
                ("Allowed Amount", allowed_amount if single_code else None, "avg_medicare_allowed_amount"),
                ("Insurance Paid", insurance_paid if single_code else None, "avg_medicare_payment"),
            ]

            for metric_name, member_value, cms_field in metrics:
                cms_value = None
                if cms_row is not None:
                    raw = cms_row.get(cms_field)
                    cms_value = None if pd.isna(raw) else float(raw)

                if member_value is None or cms_value is None:
                    diff = None
                    pct_diff = None
                else:
                    diff = float(member_value) - float(cms_value)
                    pct_diff = safe_divide(diff, cms_value) * 100

                if cms_value is None:
                    signal = "No CMS match"
                    note = "No CMS benchmark row found for this HCPCS code."
                elif member_value is None:
                    signal = "Member amount unavailable"
                    note = "Parsed EOB has multiple HCPCS lines; line-level member amounts are not extracted in this version."
                else:
                    signal = _signal_from_pct(pct_diff)
                    note = ""

                rows.append(
                    {
                        "source_type": "EOB Upload",
                        "source_file": r.get("source_file"),
                        "claim_id": r.get("claim_number"),
                        "service_date": r.get("date_of_service"),
                        "provider_name": r.get("provider"),
                        "hcpcs_code": code,
                        "service_description": "Parsed from uploaded EOB",
                        "metric": metric_name,
                        "member_value": member_value,
                        "cms_benchmark": cms_value,
                        "difference": diff,
                        "difference_pct": pct_diff,
                        "benchmark_signal": signal,
                        "cms_service_description": None if cms_row is None else cms_row.get("cms_service_description"),
                        "place_of_service": None if cms_row is None else cms_row.get("place_of_service"),
                        "benchmark_type": None if cms_row is None else cms_row.get("benchmark_type"),
                        "source_url": None if cms_row is None else cms_row.get("source_url"),
                        "analysis_note": note,
                    }
                )

    return pd.DataFrame(rows)
