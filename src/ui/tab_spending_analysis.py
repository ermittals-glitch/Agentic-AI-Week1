"""Tab 3: Healthcare Spending Analysis."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics.spending import by_category, by_month, by_provider
from src.config import TAB_DISCLAIMER
from src.data.eob_adapter import build_eob_claims_view
from src.utils.formatters import to_currency


SPEND_METRIC_MAP = {
    "Provider Charge": "provider_charge",
    "Insurance Paid": "insurance_paid",
    "Patient Responsibility": "patient_responsibility",
}


def render_tab_spending_analysis(
    claims_df: pd.DataFrame | None,
    parsed_eob_df: pd.DataFrame | None,
) -> None:
    st.subheader("Healthcare spending")
    st.caption("Understand where healthcare dollars went across services, providers, and time.")

    has_claims = claims_df is not None and not claims_df.empty
    if has_claims:
        data_for_analysis = claims_df.copy()
        source_label = "Claims workbook"
    else:
        data_for_analysis = build_eob_claims_view(parsed_eob_df)
        if data_for_analysis.empty:
            st.warning("Upload claims data or EOB files in Tab 1 to analyze spending.")
            return
        source_label = "Parsed EOB"

    metric_label = st.segmented_control(
        "Financial measure",
        list(SPEND_METRIC_MAP.keys()),
        default="Patient Responsibility",
        width="stretch",
    )
    metric_label = metric_label or "Patient Responsibility"
    metric_col = SPEND_METRIC_MAP[metric_label]

    cat_df = by_category(data_for_analysis)
    prov_df = by_provider(data_for_analysis)
    month_df = by_month(data_for_analysis)

    fig_cat = px.bar(
        cat_df,
        x="service_category",
        y=metric_col,
        color_discrete_sequence=["#147d8a"],
        labels={"service_category": "Service Category", metric_col: metric_label},
    )
    fig_cat.update_layout(showlegend=False, margin=dict(l=10, r=10, t=15, b=10), height=330)
    fig_cat.update_traces(marker_line_width=0, hovertemplate="%{x}<br>$%{y:,.2f}<extra></extra>")

    fig_prov = px.bar(
        prov_df,
        x=metric_col,
        y="provider_name",
        orientation="h",
        color_discrete_sequence=["#2d9c88"],
        labels={"provider_name": "Provider", metric_col: metric_label},
    )
    fig_prov.update_layout(showlegend=False, margin=dict(l=10, r=10, t=15, b=10), height=330)
    fig_prov.update_traces(marker_line_width=0, hovertemplate="$%{x:,.2f}<br>%{y}<extra></extra>")

    chart_col1, chart_col2 = st.columns(2, gap="medium")
    with chart_col1:
        with st.container(border=True):
            st.markdown("### By service category")
            st.caption("Which types of care account for the selected amount.")
            st.plotly_chart(fig_cat, width="stretch")
    with chart_col2:
        with st.container(border=True):
            st.markdown("### By provider")
            st.caption("Providers ranked by the selected amount.")
            st.plotly_chart(fig_prov, width="stretch")

    if month_df.empty:
        st.info("No valid service dates available for monthly trend view.")
    else:
        fig_month = px.line(
            month_df,
            x="service_month",
            y=metric_col,
            markers=True,
            labels={"service_month": "Month", metric_col: metric_label},
            color_discrete_sequence=["#126a85"],
        )
        fig_month.update_layout(showlegend=False, margin=dict(l=10, r=10, t=15, b=10), height=300)
        fig_month.update_traces(line_width=3, marker_size=8, hovertemplate="%{x}<br>$%{y:,.2f}<extra></extra>")
        with st.container(border=True):
            title_col, value_col = st.columns([0.72, 0.28], vertical_alignment="center")
            title_col.markdown("### Monthly trend")
            title_col.caption(f"Source: {source_label}")
            value_col.metric("Latest month", to_currency(month_df[metric_col].iloc[-1]))
            st.plotly_chart(fig_month, width="stretch")

    with st.expander("Data and project notice", icon=":material/info:"):
        st.caption(TAB_DISCLAIMER)
