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
    "What you may owe": "patient_responsibility",
    "What insurance paid": "insurance_paid",
}


def render_tab_spending_analysis(
    claims_df: pd.DataFrame | None,
    parsed_eob_df: pd.DataFrame | None,
) -> None:
    st.subheader("Your spending patterns")
    st.caption("See which types of care and providers account for the amounts in your uploaded claims.")

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
        "Show",
        list(SPEND_METRIC_MAP.keys()),
        default="What you may owe",
        width="stretch",
    )
    metric_label = metric_label or "What you may owe"
    metric_col = SPEND_METRIC_MAP[metric_label]

    cat_df = by_category(data_for_analysis)
    prov_df = by_provider(data_for_analysis)
    month_df = by_month(data_for_analysis)
    cat_df = cat_df.sort_values(metric_col, ascending=False)
    prov_df = prov_df.sort_values(metric_col, ascending=True)

    claim_count = data_for_analysis["claim_id"].nunique()
    if claim_count <= 1:
        total_amount = float(data_for_analysis[metric_col].sum())
        with st.container(border=True):
            st.markdown("### One claim is available")
            st.metric(metric_label, to_currency(total_amount))
            st.write(
                "Spending patterns become useful after you upload multiple claims. For this claim, use "
                "**Understand a claim** to see how the amounts were allocated."
            )
        with st.expander("Data and project notice", icon=":material/info:"):
            st.caption(TAB_DISCLAIMER)
        return

    top_category = cat_df.iloc[0]
    top_provider = prov_df.iloc[-1]
    top_category_amount = to_currency(top_category[metric_col]).replace("$", r"\$")
    top_provider_amount = to_currency(top_provider[metric_col]).replace("$", r"\$")
    st.info(
        f"Your largest {metric_label.lower()} category is **{top_category['service_category']}** "
        f"({top_category_amount}). The provider with the largest amount is "
        f"**{top_provider['provider_name']}** ({top_provider_amount}).",
        icon=":material/insights:",
    )

    chart_font = dict(family="IBM Plex Sans, Segoe UI, sans-serif", color="#344b5c", size=13)
    axis_style = dict(
        title_font=dict(color="#344b5c", size=13),
        tickfont=dict(color="#344b5c", size=12),
        gridcolor="#dce7ed",
        zerolinecolor="#c8d6df",
    )

    fig_cat = px.bar(
        cat_df,
        x="service_category",
        y=metric_col,
        color_discrete_sequence=["#147d8a"],
        labels={"service_category": "Type of care", metric_col: metric_label},
    )
    fig_cat.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=15, b=10),
        height=330,
        font=chart_font,
        xaxis=axis_style,
        yaxis=axis_style,
    )
    fig_cat.update_traces(marker_line_width=0, hovertemplate="%{x}<br>$%{y:,.2f}<extra></extra>")

    fig_prov = px.bar(
        prov_df,
        x=metric_col,
        y="provider_name",
        orientation="h",
        color_discrete_sequence=["#2d9c88"],
        labels={"provider_name": "Provider", metric_col: metric_label},
    )
    fig_prov.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=15, b=10),
        height=330,
        font=chart_font,
        xaxis=axis_style,
        yaxis=axis_style,
    )
    fig_prov.update_traces(marker_line_width=0, hovertemplate="$%{x:,.2f}<br>%{y}<extra></extra>")

    chart_col1, chart_col2 = st.columns(2, gap="medium")
    with chart_col1:
        with st.container(border=True):
            st.markdown("### By type of care")
            st.caption(f"How your {metric_label.lower()} is distributed across services.")
            st.plotly_chart(fig_cat, width="stretch")
    with chart_col2:
        with st.container(border=True):
            st.markdown("### By provider")
            st.caption(f"How your {metric_label.lower()} is distributed across providers.")
            st.plotly_chart(fig_prov, width="stretch")

    if month_df["service_month"].nunique() >= 2:
        fig_month = px.line(
            month_df,
            x="service_month",
            y=metric_col,
            markers=True,
            labels={"service_month": "Month", metric_col: metric_label},
            color_discrete_sequence=["#126a85"],
        )
        fig_month.update_layout(
            showlegend=False,
            margin=dict(l=10, r=10, t=15, b=10),
            height=300,
            font=chart_font,
            xaxis=axis_style,
            yaxis=axis_style,
        )
        fig_month.update_traces(line_width=3, marker_size=8, hovertemplate="%{x}<br>$%{y:,.2f}<extra></extra>")
        with st.container(border=True):
            title_col, value_col = st.columns([0.72, 0.28], vertical_alignment="center")
            title_col.markdown("### Monthly trend")
            title_col.caption(f"Source: {source_label}")
            value_col.metric("Latest month", to_currency(month_df[metric_col].iloc[-1]))
            st.plotly_chart(fig_month, width="stretch")

    with st.container(border=True):
        st.markdown("### How to use this information")
        st.write(
            "Use these patterns to identify your biggest cost areas. For future non-emergency care, ask your insurer "
            "about in-network options and ask the provider for an estimate before the service."
        )

    with st.expander("Data and project notice", icon=":material/info:"):
        st.caption(TAB_DISCLAIMER)
