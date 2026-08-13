"""Tab 5: Cost Benchmark against CMS public reference data."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analytics.benchmark import (
    build_claims_benchmark_analysis,
    build_eob_benchmark_analysis,
)
from src.config import TAB_DISCLAIMER
from src.utils.formatters import to_currency


SIGNAL_ABOVE = "Above benchmark"
SIGNAL_NEAR = "Near benchmark"
SIGNAL_BELOW = "Below benchmark"
SIGNAL_NO_MATCH = "No CMS match"
SIGNAL_MEMBER_UNAVAILABLE = "Member amount unavailable"


def _format_benchmark_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    money_cols = ["member_value", "cms_benchmark", "difference"]
    for col in money_cols:
        if col in out.columns:
            out[col] = out[col].apply(to_currency)
    if "difference_pct" in out.columns:
        out["difference_pct"] = out["difference_pct"].map(
            lambda x: "N/A" if pd.isna(x) else f"{x:.1f}%"
        )
    return out


def _count_signal(df: pd.DataFrame, signal_name: str) -> int:
    return int((df["benchmark_signal"] == signal_name).sum())


def _build_group_signal_table(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    table = (
        df.groupby([group_col, "benchmark_signal"], dropna=False)
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    for col in [
        SIGNAL_ABOVE,
        SIGNAL_NEAR,
        SIGNAL_BELOW,
        SIGNAL_NO_MATCH,
        SIGNAL_MEMBER_UNAVAILABLE,
    ]:
        if col not in table.columns:
            table[col] = 0

    table["Needs Review"] = table[SIGNAL_NO_MATCH] + table[SIGNAL_MEMBER_UNAVAILABLE]
    ordered_cols = [
        group_col,
        SIGNAL_ABOVE,
        SIGNAL_NEAR,
        SIGNAL_BELOW,
        "Needs Review",
    ]
    return table[ordered_cols]


def render_tab_cost_benchmark(
    claims_df: pd.DataFrame | None,
    cms_df: pd.DataFrame | None,
    parsed_eob_df: pd.DataFrame | None,
) -> None:
    st.subheader("CMS Medicare Public Benchmark")
    st.caption(
        "Public Medicare data provided for cost context. Commercial negotiated rates may differ."
    )

    if cms_df is None or cms_df.empty:
        st.warning(
            "CMS Medicare Public Benchmark data is currently unavailable. Re-upload data to reload the reference set."
        )
        return

    has_claims = claims_df is not None and not claims_df.empty
    has_eob = parsed_eob_df is not None and not parsed_eob_df.empty
    if not has_claims and not has_eob:
        st.warning("Upload claims workbook and/or EOB files in Tab 1 to run benchmark analysis.")
        return

    analysis_frames: list[pd.DataFrame] = []
    if has_claims:
        analysis_frames.append(build_claims_benchmark_analysis(claims_df, cms_df))
    if has_eob:
        analysis_frames.append(build_eob_benchmark_analysis(parsed_eob_df, cms_df))

    if not analysis_frames:
        st.warning("No benchmark analysis rows could be produced from uploaded data.")
        return

    all_analysis = pd.concat(analysis_frames, ignore_index=True)
    if all_analysis.empty:
        st.warning("No benchmark analysis rows could be produced from uploaded data.")
        return

    source_options = ["All"] + sorted(all_analysis["source_type"].dropna().unique().tolist())
    metric_options = sorted(all_analysis["metric"].dropna().unique().tolist())

    with st.container(border=True):
        f1, f2 = st.columns(2)
        source_filter = f1.selectbox("Data source", source_options)
        metric_filter = f2.multiselect("Financial measures", metric_options, default=metric_options)

    filtered = all_analysis.copy()
    if source_filter != "All":
        filtered = filtered[filtered["source_type"] == source_filter]
    if metric_filter:
        filtered = filtered[filtered["metric"].isin(metric_filter)]

    if filtered.empty:
        st.info("No rows match selected filters.")
        return

    above_count = _count_signal(filtered, SIGNAL_ABOVE)
    near_count = _count_signal(filtered, SIGNAL_NEAR)
    below_count = _count_signal(filtered, SIGNAL_BELOW)
    needs_review_count = _count_signal(filtered, SIGNAL_NO_MATCH) + _count_signal(
        filtered, SIGNAL_MEMBER_UNAVAILABLE
    )

    st.markdown("### Benchmark snapshot")
    kpi_cols = st.columns(4, gap="medium")
    kpi_cols[0].metric("Above benchmark", f"{above_count:,}", border=True)
    kpi_cols[1].metric("Near benchmark", f"{near_count:,}", border=True)
    kpi_cols[2].metric("Below benchmark", f"{below_count:,}", border=True)
    kpi_cols[3].metric("Needs review", f"{needs_review_count:,}", border=True)
    st.caption(
        f"{filtered['claim_id'].nunique()} claims  •  {filtered['hcpcs_code'].nunique()} HCPCS codes  •  "
        f"{len(filtered):,} comparison rows"
    )

    by_source = _build_group_signal_table(filtered, "source_type")
    by_metric = _build_group_signal_table(filtered, "metric")

    with st.expander("Grouped benchmark summary", icon=":material/analytics:"):
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("**By source**")
            st.dataframe(by_source, width="stretch", hide_index=True)
        with g2:
            st.markdown("**By financial measure**")
            st.dataframe(by_metric, width="stretch", hide_index=True)

    display_cols = [
        "source_type",
        "source_file",
        "claim_id",
        "service_date",
        "provider_name",
        "hcpcs_code",
        "service_description",
        "metric",
        "member_value",
        "cms_benchmark",
        "difference",
        "difference_pct",
        "benchmark_signal",
        "cms_service_description",
        "place_of_service",
        "analysis_note",
    ]
    display = _format_benchmark_df(filtered[display_cols].copy())

    st.markdown("### Service-level comparison")
    st.dataframe(
        display,
        width="stretch",
        hide_index=True,
        column_config={
            "member_value": st.column_config.TextColumn("Your value"),
            "cms_benchmark": st.column_config.TextColumn("CMS benchmark"),
            "difference": st.column_config.TextColumn("Difference"),
            "difference_pct": st.column_config.TextColumn("Variance"),
            "benchmark_signal": st.column_config.TextColumn("Result"),
            "source_url": st.column_config.LinkColumn("CMS source"),
        },
    )

    with st.expander("CMS source references", icon=":material/open_in_new:"):
        reference_cols = [
            "hcpcs_code",
            "cms_service_description",
            "benchmark_type",
            "source_url",
        ]
        ref_df = filtered[reference_cols].drop_duplicates().sort_values("hcpcs_code")
        st.dataframe(
            ref_df,
            width="stretch",
            hide_index=True,
            column_config={"source_url": st.column_config.LinkColumn("CMS source")},
        )

    with st.expander("How to interpret this comparison", icon=":material/info:"):
        st.write(
            "The CMS Medicare Public Benchmark contains public Medicare averages, not commercial negotiated plan rates "
            "or a final bill. Use it as directional cost context when reviewing a service."
        )
        st.caption(TAB_DISCLAIMER)
