"""Tab 2: Claims Overview."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analytics.kpis import build_claim_kpis
from src.config import FIELD_LABELS, TAB_DISCLAIMER
from src.data.eob_adapter import build_eob_claims_view
from src.utils.formatters import to_currency


def _rename_for_display(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns=FIELD_LABELS)


def render_tab_overview(
    claims_df: pd.DataFrame | None,
    parsed_eob_df: pd.DataFrame | None,
) -> None:
    st.subheader("Claims overview")
    st.caption("A clear financial summary of your uploaded healthcare activity.")

    has_claims = claims_df is not None and not claims_df.empty
    if has_claims:
        data_for_overview = claims_df.copy()
        source_label = "Claims workbook"
    else:
        data_for_overview = build_eob_claims_view(parsed_eob_df)
        if data_for_overview.empty:
            st.warning("Upload claims data or EOB files in Tab 1 to see member claims overview.")
            return
        source_label = "Parsed EOB"

    if data_for_overview is None or data_for_overview.empty:
        st.warning("No records available for overview.")
        return

    kpis = build_claim_kpis(data_for_overview)
    st.caption(
        f"Source: {source_label}  •  {kpis['claim_count']} claims  •  {kpis['service_lines']} service lines"
    )

    kpi_cols = st.columns(4, gap="medium")
    kpi_cols[0].metric(
        "Provider billed",
        to_currency(kpis["total_provider_charge"]),
        help="Total amount submitted by providers before plan discounts.",
        border=True,
    )
    kpi_cols[1].metric(
        "Plan allowed",
        to_currency(kpis["total_allowed"]),
        help="Total amount recognized by the plan for payment.",
        border=True,
    )
    kpi_cols[2].metric(
        "Insurance paid",
        to_currency(kpis["total_insurance_paid"]),
        help="Total amount paid by the health plan.",
        border=True,
    )
    kpi_cols[3].metric(
        "Your responsibility",
        to_currency(kpis["total_patient_responsibility"]),
        help="Total amount assigned to the member or another payer.",
        border=True,
    )

    st.markdown("### Explore claims")
    providers = ["All"] + sorted(data_for_overview["provider_name"].dropna().unique().tolist())
    categories = ["All"] + sorted(data_for_overview["service_category"].dropna().unique().tolist())
    statuses = ["All"] + sorted(data_for_overview["claim_status"].dropna().unique().tolist())

    with st.container(border=True):
        f1, f2, f3 = st.columns(3)
        provider_filter = f1.selectbox("Provider", providers)
        category_filter = f2.selectbox("Service category", categories)
        status_filter = f3.selectbox("Claim status", statuses)

    filtered = data_for_overview.copy()
    if provider_filter != "All":
        filtered = filtered[filtered["provider_name"] == provider_filter]
    if category_filter != "All":
        filtered = filtered[filtered["service_category"] == category_filter]
    if status_filter != "All":
        filtered = filtered[filtered["claim_status"] == status_filter]

    st.markdown("### Claim details")
    display_df = _rename_for_display(filtered).copy()
    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Date of Service": st.column_config.DateColumn(format="MMM DD, YYYY"),
            "Provider Charge": st.column_config.NumberColumn(format="$%.2f"),
            "Allowed Amount": st.column_config.NumberColumn(format="$%.2f"),
            "Insurance Paid": st.column_config.NumberColumn(format="$%.2f"),
            "Deductible": st.column_config.NumberColumn(format="$%.2f"),
            "Copay": st.column_config.NumberColumn(format="$%.2f"),
            "Coinsurance": st.column_config.NumberColumn(format="$%.2f"),
            "Patient Responsibility": st.column_config.NumberColumn(format="$%.2f"),
        },
    )

    with st.expander("Data and project notice", icon=":material/info:"):
        st.caption(TAB_DISCLAIMER)
