"""Tab 1: Upload EOB / Claim Data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import GLOBAL_DISCLAIMER_LINES, TAB_DISCLAIMER
from src.data.loaders import DataLoadError, load_claims_excel, load_default_cms_reference
from src.parsers.eob_pdf_parser import parse_eob_document
from src.utils.text_helpers import build_disclaimer_block


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_EOB_PATH = PROJECT_ROOT / "Sample_EOB_Vision_CMS_Data.pdf"
SAMPLE_CLAIMS_PATH = PROJECT_ROOT / "Healthcare_Claims_Analytics_Demo_Data.xlsx"


def _activate_claims_workbook(file_bytes: bytes) -> None:
    member_df, claims_df, cms_df, cms_source = load_claims_excel(file_bytes)
    st.session_state["member_info"] = member_df
    st.session_state["claims_df"] = claims_df
    st.session_state["cms_df"] = cms_df
    st.session_state["cms_source"] = cms_source
    st.session_state["data_quality_report"] = None
    st.session_state["data_ready"] = True
    st.session_state["next_active_tab"] = "2. Claims Overview"
    st.toast(
        f"Loaded {claims_df['claim_id'].nunique()} claims. Opening your costs.",
        icon=":material/check_circle:",
    )
    st.rerun()


def _activate_eob_records(parsed_records: list[dict]) -> None:
    parsed_df = pd.DataFrame(parsed_records)
    validated_mask = parsed_df["extraction_confidence"].eq("Validated")
    validated_df = parsed_df[validated_mask].copy()
    needs_review_df = parsed_df[~validated_mask]

    if not needs_review_df.empty:
        filenames = ", ".join(needs_review_df["source_file"].astype(str).tolist())
        st.warning(
            f"We could not confidently read all financial amounts in: {filenames}. "
            "Those files were not included in the analysis. Try a clearer document or upload a claims workbook.",
            icon=":material/warning:",
        )

    if validated_df.empty:
        return

    st.session_state["parsed_eob_records"] = validated_df
    if st.session_state.get("cms_df") is None or st.session_state.get("cms_df").empty:
        st.session_state["cms_df"] = load_default_cms_reference()
        st.session_state["cms_source"] = "built_in"

    st.session_state["data_ready"] = True
    st.session_state["next_active_tab"] = "2. Claims Overview"
    st.toast(
        f"Read {len(validated_df)} EOB file{'s' if len(validated_df) != 1 else ''}. Opening your costs.",
        icon=":material/check_circle:",
    )
    st.rerun()


def _render_initial_combined_disclaimer() -> None:
    with st.expander("Important disclaimer", expanded=True, icon=":material/warning:"):
        lines = GLOBAL_DISCLAIMER_LINES + [TAB_DISCLAIMER]
        st.markdown(build_disclaimer_block(lines))


def _render_value_cards() -> None:
    value_cols = st.columns(3, gap="medium")
    cards = [
        (
            ":material/description:",
            "Understand your claims",
            "See what the provider billed, your plan's negotiated amount, what insurance paid, and what you may owe.",
        ),
        (
            ":material/query_stats:",
            "Analyze your spending",
            "See your healthcare costs by provider, type of care, and month when you upload multiple claims.",
        ),
        (
            ":material/balance:",
            "Compare costs",
            "Compare eligible services with public Medicare averages for context, not as a billing audit.",
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
            load_sample_eob = st.button(
                "Load sample EOB",
                key=f"sample_eob_{widget_seed}",
                icon=":material/science:",
                width="stretch",
            )
            st.caption("We'll extract available claim, service, and payment information from your documents.")

    with upload_col2:
        with st.container(border=True, height="stretch"):
            st.markdown(":material/table_chart:")
            badge_col, _ = st.columns([0.55, 0.45])
            badge_col.badge("Best for multiple claims", icon=":material/recommend:", color="blue")
            st.markdown("### Upload claims workbook")
            st.write("Upload structured claims data for deeper spending analytics.")
            st.caption("Excel (.xlsx)")
            claims_excel = st.file_uploader(
                "Choose claims workbook",
                type=["xlsx"],
                accept_multiple_files=False,
                key=f"claims_upload_{widget_seed}",
            )
            load_sample_claims = st.button(
                "Load sample claims workbook",
                key=f"sample_claims_{widget_seed}",
                icon=":material/science:",
                width="stretch",
            )
            st.caption("Best for analyzing multiple claims, providers, service categories, and spending trends.")

    if claims_excel:
        try:
            _activate_claims_workbook(claims_excel.read())

        except DataLoadError as exc:
            st.error(f"Could not load workbook: {exc}")
        except Exception as exc:
            st.error(f"Unexpected error while reading workbook: {exc}")

    if load_sample_claims:
        try:
            _activate_claims_workbook(SAMPLE_CLAIMS_PATH.read_bytes())
        except (DataLoadError, OSError) as exc:
            st.error(f"Could not load the sample claims workbook: {exc}")

    if eob_files:
        _activate_eob_records([parse_eob_document(file.name, file.read()) for file in eob_files])

    if load_sample_eob:
        try:
            _activate_eob_records(
                [parse_eob_document(SAMPLE_EOB_PATH.name, SAMPLE_EOB_PATH.read_bytes())]
            )
        except OSError as exc:
            st.error(f"Could not load the sample EOB: {exc}")

    if not st.session_state.get("data_ready"):
        _render_initial_combined_disclaimer()
