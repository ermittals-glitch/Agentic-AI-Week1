"""Tab 1: Upload EOB / Claim Data."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config import GLOBAL_DISCLAIMER_LINES, TAB_DISCLAIMER
from src.data.loaders import DataLoadError, load_claims_excel, load_default_cms_reference
from src.parsers.eob_pdf_parser import parse_eob_document
from src.utils.text_helpers import build_disclaimer_block


def _render_initial_combined_disclaimer() -> None:
    with st.expander("Important Disclaimer", expanded=False):
        lines = GLOBAL_DISCLAIMER_LINES + [TAB_DISCLAIMER]
        st.markdown(build_disclaimer_block(lines))


def _render_value_cards() -> None:
    value_cols = st.columns(3, gap="medium")
    cards = [
        (
            ":material/description:",
            "Understand your claims",
            "See provider charges, allowed amounts, insurance payments, and your responsibility in one place.",
        ),
        (
            ":material/query_stats:",
            "Analyze your spending",
            "Explore healthcare costs by provider, service category, and time period.",
        ),
        (
            ":material/balance:",
            "Compare costs",
            "Compare eligible procedures against public CMS Medicare cost benchmarks for additional context.",
        ),
    ]
    for column, (icon, title, description) in zip(value_cols, cards):
        with column:
            with st.container(border=True, height="stretch"):
                st.markdown(icon)
                st.markdown(f"### {title}")
                st.write(description)


def render_tab_upload() -> None:
    _render_value_cards()

    st.markdown("## Start with your healthcare data")
    st.write(
        "Choose either option below. Upload EOB documents, a claims workbook, or both for a more complete analysis."
    )

    widget_seed = int(st.session_state.get("upload_widget_seed", 0))

    upload_col1, upload_col2 = st.columns(2, gap="large")

    with upload_col1:
        with st.container(border=True, height="stretch"):
            st.markdown(":material/description:")
            st.markdown("### Upload EOB documents")
            st.write("Upload one or more Explanation of Benefits documents.")
            st.caption("PDF · JPG · JPEG · PNG")
            eob_files = st.file_uploader(
                "Choose EOB files",
                type=["pdf", "jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key=f"eob_upload_{widget_seed}",
            )
            st.caption("We'll extract available claim, service, and payment information from your documents.")

    with upload_col2:
        with st.container(border=True, height="stretch"):
            st.markdown(":material/table_chart:")
            badge_col, _ = st.columns([0.55, 0.45])
            badge_col.badge("Recommended for analytics", icon=":material/recommend:", color="blue")
            st.markdown("### Upload claims workbook")
            st.write("Upload structured claims data for deeper spending analytics.")
            st.caption("Excel (.xlsx)")
            claims_excel = st.file_uploader(
                "Choose claims workbook",
                type=["xlsx"],
                accept_multiple_files=False,
                key=f"claims_upload_{widget_seed}",
            )
            st.caption("Best for analyzing multiple claims, providers, service categories, and spending trends.")

    if claims_excel:
        try:
            member_df, claims_df, cms_df, cms_source = load_claims_excel(claims_excel.read())
            st.session_state["member_info"] = member_df
            st.session_state["claims_df"] = claims_df
            st.session_state["cms_df"] = cms_df
            st.session_state["cms_source"] = cms_source
            st.session_state["data_quality_report"] = None
            st.session_state["data_ready"] = True
            st.session_state["next_active_tab"] = "2. Claims Overview"
            st.success("Claims data loaded successfully.")

            if cms_source == "built_in":
                st.info(
                    "Using the CMS Medicare Public Benchmark for cost context. Commercial negotiated rates may differ."
                )
            else:
                st.info("Using CMS Medicare Public Benchmark data from the uploaded workbook.")

            with st.expander("Preview claims data"):
                st.dataframe(claims_df, width="stretch")
            with st.expander("Preview CMS reference data"):
                st.dataframe(cms_df, width="stretch")
            if not member_df.empty:
                with st.expander("Preview member info"):
                    st.dataframe(member_df, width="stretch")

            st.success("Your data is processed. Opening Claims Overview...")
            st.rerun()

        except DataLoadError as exc:
            st.error(f"Could not load workbook: {exc}")
        except Exception as exc:
            st.error(f"Unexpected error while reading workbook: {exc}")

    if eob_files:
        parsed_records = []
        for file in eob_files:
            parsed_records.append(parse_eob_document(file.name, file.read()))

        parsed_df = pd.DataFrame(parsed_records)
        st.session_state["parsed_eob_records"] = parsed_df

        if st.session_state.get("cms_df") is None or st.session_state.get("cms_df").empty:
            st.session_state["cms_df"] = load_default_cms_reference()
            st.session_state["cms_source"] = "built_in"

        st.success(f"Parsed {len(parsed_df)} EOB file(s).")
        st.dataframe(parsed_df.drop(columns=["raw_text"], errors="ignore"), width="stretch")

        st.session_state["data_ready"] = True
        st.session_state["next_active_tab"] = "2. Claims Overview"
        st.success("Your data is processed. Opening Claims Overview...")
        st.rerun()

    if not st.session_state.get("data_ready"):
        _render_initial_combined_disclaimer()
