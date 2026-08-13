"""Tab 4: EOB Explainer."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analytics.explainer import explain_claim_line
from src.config import TAB_DISCLAIMER
from src.data.eob_adapter import build_eob_claims_view
from src.utils.formatters import to_currency
from src.utils.text_helpers import GLOSSARY


def render_tab_eob_explainer(claims_df: pd.DataFrame | None, parsed_eob_df: pd.DataFrame | None) -> None:
    st.subheader("EOB explainer")
    st.caption("Turn healthcare billing language into a clear explanation of what happened and why.")

    has_claims = claims_df is not None and not claims_df.empty
    if has_claims:
        data_for_explainer = claims_df.copy()
        source_caption = "Explaining a service line from your claims workbook."
    else:
        data_for_explainer = build_eob_claims_view(parsed_eob_df)
        if data_for_explainer.empty:
            st.warning("Upload claims data or EOB files in Tab 1 to use the EOB explainer.")
            return
        source_caption = (
            "Explaining a parsed EOB summary. Deductible, copay, or coinsurance may be unavailable for some formats."
        )

    st.caption(source_caption)

    claim_ids = sorted(data_for_explainer["claim_id"].unique().tolist())
    selector_col1, selector_col2 = st.columns(2)
    selected_claim = selector_col1.selectbox("Claim number", claim_ids)

    claim_slice = data_for_explainer[data_for_explainer["claim_id"] == selected_claim].copy()

    if claim_slice.empty:
        st.warning("No records found for selected claim.")
        return

    service_options = claim_slice["service_description"].tolist()
    selected_service = selector_col2.selectbox("Service line", service_options)
    selected_row = claim_slice[claim_slice["service_description"] == selected_service].iloc[0]

    summary_cols = st.columns(4, gap="medium")
    summary_cols[0].metric("Provider billed", to_currency(selected_row["provider_charge"]), border=True)
    summary_cols[1].metric("Plan allowed", to_currency(selected_row["allowed_amount"]), border=True)
    summary_cols[2].metric("Insurance paid", to_currency(selected_row["insurance_paid"]), border=True)
    summary_cols[3].metric(
        "Your responsibility",
        to_currency(selected_row["patient_responsibility"]),
        border=True,
    )

    detail_col1, detail_col2 = st.columns([0.58, 0.42], gap="medium")
    with detail_col1:
        with st.container(border=True):
            st.markdown("### What this claim means")
            st.write(explain_claim_line(selected_row))
            st.caption(
                f"Provider: {selected_row['provider_name']}  •  HCPCS: {selected_row['hcpcs_code']}  •  "
                f"Status: {selected_row['claim_status']}"
            )
    with detail_col2:
        with st.container(border=True):
            st.markdown("### Your cost share")
            cost_share = pd.DataFrame(
                {
                    "Cost component": ["Deductible", "Copay", "Coinsurance"],
                    "Amount": [
                        selected_row["deductible"],
                        selected_row["copay"],
                        selected_row["coinsurance"],
                    ],
                }
            )
            st.dataframe(
                cost_share,
                width="stretch",
                hide_index=True,
                column_config={
                    "Amount": st.column_config.NumberColumn(format="$%.2f"),
                },
            )

    with st.expander("Healthcare cost glossary", icon=":material/menu_book:"):
        for term, meaning in GLOSSARY.items():
            st.markdown(f"**{term}**  \\  {meaning}")

    if parsed_eob_df is not None and not parsed_eob_df.empty:
        with st.expander("Parsed EOB source details", icon=":material/description:"):
            st.dataframe(
                parsed_eob_df.drop(columns=["raw_text"], errors="ignore"),
                width="stretch",
                hide_index=True,
            )

    with st.expander("Data and project notice", icon=":material/info:"):
        st.caption(TAB_DISCLAIMER)
