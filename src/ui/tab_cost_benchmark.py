"""Member-focused comparison with CMS Medicare public reference data."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analytics.benchmark import (
    build_claims_benchmark_analysis,
    build_eob_benchmark_analysis,
)
from src.config import TAB_DISCLAIMER
from src.utils.formatters import to_currency_or_na


def _comparison_label(row: pd.Series) -> str:
    provider = str(row.get("provider_name") or "Provider not identified")
    service = str(row.get("service_description") or row.get("cms_service_description") or "Service")
    return f"{provider} · {service}"


def render_tab_cost_benchmark(
    claims_df: pd.DataFrame | None,
    cms_df: pd.DataFrame | None,
    parsed_eob_df: pd.DataFrame | None,
) -> None:
    st.subheader("Compare a service with Medicare")
    st.caption("Use public Medicare averages as context for one service at a time.")
    st.info(
        "This is not a fair-price test or billing audit. Commercial insurance plans negotiate different rates, "
        "and costs higher than Medicare are common.",
        icon=":material/info:",
    )

    if cms_df is None or cms_df.empty:
        st.warning("Medicare reference data is unavailable. Re-upload your information to reload it.")
        return

    has_claims = claims_df is not None and not claims_df.empty
    has_eob = parsed_eob_df is not None and not parsed_eob_df.empty
    if not has_claims and not has_eob:
        st.warning("Upload a claims file or EOB before comparing a service.")
        return

    analysis_frames: list[pd.DataFrame] = []
    if has_claims:
        analysis_frames.append(build_claims_benchmark_analysis(claims_df, cms_df))
    if has_eob:
        analysis_frames.append(build_eob_benchmark_analysis(parsed_eob_df, cms_df))

    comparisons = pd.concat(analysis_frames, ignore_index=True)
    comparisons = comparisons[comparisons["metric"] == "Allowed Amount"].reset_index(drop=True)
    comparisons = comparisons[comparisons["cms_benchmark"].notna()].reset_index(drop=True)
    if comparisons.empty:
        st.info("None of the uploaded services matched the available Medicare reference data.")
        return

    comparison_ids = comparisons.index.tolist()
    selected_id = st.pills(
        "Choose a service",
        comparison_ids,
        default=comparison_ids[0],
        format_func=lambda row_id: _comparison_label(comparisons.loc[row_id]),
        selection_mode="single",
    )
    selected_id = comparison_ids[0] if selected_id is None else selected_id
    selected = comparisons.loc[selected_id]

    member_value = selected.get("member_value")
    medicare_value = selected.get("cms_benchmark")
    difference = selected.get("difference")
    difference_pct = selected.get("difference_pct")

    metric_cols = st.columns(3, gap="medium")
    metric_cols[0].metric("Your plan's negotiated amount", to_currency_or_na(member_value), border=True)
    metric_cols[1].metric("Medicare public average", to_currency_or_na(medicare_value), border=True)
    metric_cols[2].metric("Difference", to_currency_or_na(difference), border=True)

    with st.container(border=True):
        st.markdown("### What this comparison means")
        if pd.isna(member_value):
            st.write(
                "The EOB did not provide a reliable service-level amount for this comparison. "
                "Use a structured claims file or ask your insurer for the allowed amount."
            )
        elif pd.isna(medicare_value):
            st.write("No Medicare average was available for this insurance service code.")
        else:
            direction = str(selected.get("benchmark_signal") or "Comparison available")
            variance_text = "" if pd.isna(difference_pct) else f" ({abs(float(difference_pct)):.1f}% difference)"
            st.write(
                f"This service is **{direction.lower()}**{variance_text}. This does not mean the charge is right or wrong. "
                "Medicare and commercial plans use different payment rules and negotiated rates."
            )

    with st.container(border=True):
        st.markdown("### What you can do with this information")
        st.write(
            "If you have questions, contact your insurer with the claim number and ask how the negotiated amount was determined. "
            "For future non-emergency care, ask about in-network providers and request an estimate before the service."
        )

    with st.expander("Reference details", icon=":material/open_in_new:"):
        st.write(f"Insurance service code: {selected.get('hcpcs_code') or 'Not available'}")
        st.write(f"Medicare service: {selected.get('cms_service_description') or 'Not available'}")
        st.write(f"Place of service: {selected.get('place_of_service') or 'Not available'}")
        st.write(f"Reference type: {selected.get('benchmark_type') or 'Not available'}")
        source_url = selected.get("source_url")
        if source_url and not pd.isna(source_url):
            st.link_button("Open CMS source", str(source_url), icon=":material/open_in_new:")

    with st.expander("Data and project notice", icon=":material/info:"):
        st.caption(TAB_DISCLAIMER)
