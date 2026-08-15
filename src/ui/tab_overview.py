"""Tab 2: Claims Overview."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analytics.kpis import build_claim_kpis
from src.config import TAB_DISCLAIMER
from src.data.eob_adapter import build_eob_claims_view
from src.utils.formatters import to_currency


def _open_claim_explainer(claim_id: str, service_description: str) -> None:
    st.session_state["selected_claim_id"] = claim_id
    st.session_state["selected_service_description"] = service_description
    st.session_state["next_active_tab"] = "4. EOB Explainer"


def _claim_summary(claim_rows: pd.DataFrame) -> dict[str, object]:
    first = claim_rows.iloc[0]
    service_names = claim_rows["service_description"].dropna().astype(str).unique().tolist()
    return {
        "claim_id": str(first["claim_id"]),
        "provider": str(first["provider_name"]),
        "date": first["service_date"],
        "services": service_names,
        "insurance_paid": float(claim_rows["insurance_paid"].sum()),
        "may_owe": float(claim_rows["patient_responsibility"].sum()),
    }


def render_tab_overview(
    claims_df: pd.DataFrame | None,
    parsed_eob_df: pd.DataFrame | None,
) -> None:
    st.subheader("Your healthcare costs")
    st.caption("Start with what you may owe, then open any claim to understand how the amounts were allocated.")

    has_claims = claims_df is not None and not claims_df.empty
    data_for_overview = claims_df.copy() if has_claims else build_eob_claims_view(parsed_eob_df)
    if data_for_overview.empty:
        st.warning("Upload a claims file or EOB to review your costs.")
        return

    kpis = build_claim_kpis(data_for_overview)
    billed_allowed_difference = max(
        0.0,
        float(kpis["total_provider_charge"]) - float(kpis["total_allowed"]),
    )
    has_other_responsibility = (
        "responsibility_label" in data_for_overview.columns
        and data_for_overview["responsibility_label"].astype(str).str.contains("other", case=False).any()
    )
    responsibility_label = "Patient/other amount" if has_other_responsibility else "What you may owe"

    kpi_cols = st.columns(4, gap="medium")
    kpi_cols[0].metric(
        responsibility_label,
        to_currency(kpis["total_patient_responsibility"]),
        help="This is from the uploaded claim data. A provider bill, secondary insurance, or payments already made may change it.",
        border=True,
    )
    kpi_cols[1].metric("What insurance paid", to_currency(kpis["total_insurance_paid"]), border=True)
    kpi_cols[2].metric("Plan's negotiated amount", to_currency(kpis["total_allowed"]), border=True)
    kpi_cols[3].metric(
        "Difference from billed amount",
        to_currency(billed_allowed_difference),
        help="For in-network care, this commonly reflects a plan discount. Check your EOB before assuming you owe this difference.",
        border=True,
    )

    if has_other_responsibility:
        st.info(
            "This EOB labels the remaining amount as patient/other responsibility. It may include another payer and should not be treated as a final bill.",
            icon=":material/info:",
        )

    st.markdown("### Your claims")
    claim_count = data_for_overview["claim_id"].nunique()
    st.caption(
        f"{claim_count} claim{'s' if claim_count != 1 else ''} from your uploaded information. "
        "Select a claim for a plain-English explanation."
    )

    summaries = [_claim_summary(group) for _, group in data_for_overview.groupby("claim_id", sort=False)]
    card_columns = st.columns(2, gap="medium")
    for index, summary in enumerate(summaries):
        with card_columns[index % 2]:
            with st.container(border=True):
                service_names = summary["services"]
                service_text = str(service_names[0])
                if len(service_names) > 1:
                    service_text += f" and {len(service_names) - 1} more service{'s' if len(service_names) > 2 else ''}"
                date_value = summary["date"]
                date_text = date_value.strftime("%b %d, %Y") if pd.notna(date_value) else "Date not available"

                st.markdown(f"#### {summary['provider']}")
                st.caption(f"{date_text}  •  Claim {summary['claim_id']}")
                st.write(service_text)
                amount_col1, amount_col2 = st.columns(2)
                amount_col1.metric("Insurance paid", to_currency(summary["insurance_paid"]))
                amount_col2.metric(responsibility_label, to_currency(summary["may_owe"]))
                if st.button(
                    "Explain this claim",
                    key=f"explain_{summary['claim_id']}_{index}",
                    icon=":material/article:",
                    width="stretch",
                ):
                    _open_claim_explainer(str(summary["claim_id"]), str(service_names[0]))
                    st.rerun()

    with st.container(border=True):
        st.markdown("### If something does not look right")
        st.write(
            "Compare the claim with your provider bill. For payment or coverage questions, contact your insurer with the claim number. "
            "For service details, ask the provider for an itemized bill. An EOB is not itself a bill."
        )

    with st.expander("Data and project notice", icon=":material/info:"):
        st.caption(TAB_DISCLAIMER)
