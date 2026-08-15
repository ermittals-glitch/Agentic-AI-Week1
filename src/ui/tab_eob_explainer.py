"""Tab 4: EOB Explainer."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analytics.explainer import explain_claim_line
from src.config import TAB_DISCLAIMER
from src.data.eob_adapter import build_eob_claims_view
from src.utils.formatters import to_currency, to_currency_or_na
from src.utils.text_helpers import GLOSSARY


def render_tab_eob_explainer(claims_df: pd.DataFrame | None, parsed_eob_df: pd.DataFrame | None) -> None:
    st.subheader("Understand a claim")
    st.caption("Choose a claim to see how the available amounts were allocated and what the claim says you may owe.")

    has_claims = claims_df is not None and not claims_df.empty
    if has_claims:
        data_for_explainer = claims_df.copy()
        source_caption = "Based on your uploaded claims file."
    else:
        data_for_explainer = build_eob_claims_view(parsed_eob_df)
        if data_for_explainer.empty:
            st.warning("Upload claims data or EOB files in Tab 1 to use the EOB explainer.")
            return
        source_caption = "Based on information confidently extracted from your EOB. Some cost-share details may be unavailable."

    st.caption(source_caption)

    claim_ids = sorted(data_for_explainer["claim_id"].unique().tolist())
    preferred_claim = st.session_state.get("selected_claim_id")
    default_claim = preferred_claim if preferred_claim in claim_ids else claim_ids[0]
    claim_labels = {
        claim_id: f"{data_for_explainer[data_for_explainer['claim_id'] == claim_id].iloc[0]['provider_name']} · {claim_id}"
        for claim_id in claim_ids
    }
    selected_claim = st.pills(
        "Choose a claim",
        claim_ids,
        default=default_claim,
        format_func=lambda claim_id: claim_labels[claim_id],
        selection_mode="single",
    )
    selected_claim = selected_claim or default_claim
    st.session_state["selected_claim_id"] = selected_claim

    claim_slice = data_for_explainer[data_for_explainer["claim_id"] == selected_claim].copy()

    if claim_slice.empty:
        st.warning("No records found for selected claim.")
        return

    service_options = claim_slice["service_description"].tolist()
    preferred_service = st.session_state.get("selected_service_description")
    default_service = preferred_service if preferred_service in service_options else service_options[0]
    if len(service_options) > 1:
        selected_service = st.pills(
            "Choose a service",
            service_options,
            default=default_service,
            selection_mode="single",
        )
        selected_service = selected_service or default_service
    else:
        selected_service = default_service
    st.session_state["selected_service_description"] = selected_service
    selected_row = claim_slice[claim_slice["service_description"] == selected_service].iloc[0]

    responsibility_label = str(selected_row.get("responsibility_label", "What you may owe"))
    member_amount_label = "Patient/other amount" if "other" in responsibility_label.lower() else "What you may owe"
    negotiated_difference = max(0.0, float(selected_row["provider_charge"]) - float(selected_row["allowed_amount"]))

    summary_cols = st.columns(4, gap="medium")
    summary_cols[0].metric(
        member_amount_label,
        to_currency(selected_row["patient_responsibility"]),
        border=True,
    )
    summary_cols[1].metric("What insurance paid", to_currency(selected_row["insurance_paid"]), border=True)
    summary_cols[2].metric("Plan's negotiated amount", to_currency(selected_row["allowed_amount"]), border=True)
    summary_cols[3].metric("Difference from billed amount", to_currency(negotiated_difference), border=True)

    detail_col1, detail_col2 = st.columns([0.58, 0.42], gap="medium")
    with detail_col1:
        with st.container(border=True):
            st.markdown("### What this claim means")
            explanation = explain_claim_line(selected_row).replace("$", r"\$")
            st.markdown(explanation)
            st.caption(
                f"Provider: {selected_row['provider_name']}  •  Service: {selected_row['service_description']}"
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
            known_cost_share = cost_share.dropna(subset=["Amount"])
            available_cost_share = known_cost_share[known_cost_share["Amount"] > 0]
            if available_cost_share.empty and known_cost_share.empty:
                st.info("This EOB did not provide a reliable deductible, copay, and coinsurance breakdown.")
            elif available_cost_share.empty:
                st.info("No deductible, copay, or coinsurance was shown for this service.")
            else:
                st.dataframe(
                    available_cost_share,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "Amount": st.column_config.NumberColumn(format="$%.2f"),
                    },
                )
            st.caption(f"Claim amount shown: {member_amount_label} {to_currency_or_na(selected_row['patient_responsibility'])}")

    with st.container(border=True):
        st.markdown("### What you can do next")
        st.markdown(
            "- Confirm that you recognize the provider, date, and service.\n"
            "- Compare this EOB with any bill from the provider; an EOB is not a bill.\n"
            "- For coverage or payment questions, contact your insurer and provide the claim number.\n"
            "- If you do not recognize the service, contact your insurer promptly."
        )

    with st.expander("Healthcare cost glossary", icon=":material/menu_book:"):
        for term, meaning in GLOSSARY.items():
            st.markdown(f"**{term}**  \\  {meaning}")

    with st.expander("Claim reference details", icon=":material/description:"):
        st.write(f"Claim number: {selected_row['claim_id']}")
        st.write(f"Insurance service code: {selected_row['hcpcs_code'] or 'Not available'}")
        st.write(f"Extraction/status: {selected_row['claim_status']}")

    with st.expander("Data and project notice", icon=":material/info:"):
        st.caption(TAB_DISCLAIMER)
