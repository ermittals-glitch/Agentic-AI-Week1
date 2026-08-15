from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.config import APP_SUBTITLE, APP_TITLE
from src.ui.tab_cost_benchmark import render_tab_cost_benchmark
from src.ui.tab_eob_explainer import render_tab_eob_explainer
from src.ui.tab_overview import render_tab_overview
from src.ui.tab_spending_analysis import render_tab_spending_analysis
from src.ui.tab_upload import render_tab_upload


TAB_1 = "1. Upload EOB/Claim Data"
TAB_2 = "2. Claims Overview"
TAB_3 = "3. Healthcare Spending Analysis"
TAB_4 = "4. EOB Explainer"
TAB_5 = "5. Cost Benchmark"

NAV_LABELS = {
    TAB_1: "Upload documents",
    TAB_2: "Your costs",
    TAB_4: "Understand a claim",
    TAB_3: "Spending patterns",
    TAB_5: "Compare with Medicare",
}


def _load_local_css() -> None:
    css_file = Path("assets/styles/custom.css")
    if css_file.exists():
        st.markdown(f"<style>{css_file.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def _init_session_state() -> None:
    defaults = {
        "claims_df": None,
        "cms_df": None,
        "member_info": None,
        "parsed_eob_records": None,
        "data_quality_report": None,
        "cms_source": None,
        "data_ready": False,
        "active_tab": TAB_1,
        "next_active_tab": None,
        "selected_claim_id": None,
        "selected_service_description": None,
        "upload_widget_seed": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _clear_analysis_state() -> None:
    st.session_state["claims_df"] = None
    st.session_state["cms_df"] = None
    st.session_state["member_info"] = None
    st.session_state["parsed_eob_records"] = None
    st.session_state["data_quality_report"] = None
    st.session_state["cms_source"] = None
    st.session_state["data_ready"] = False
    st.session_state["active_tab"] = TAB_1
    st.session_state["selected_claim_id"] = None
    st.session_state["selected_service_description"] = None
    st.session_state["upload_widget_seed"] = int(st.session_state.get("upload_widget_seed", 0)) + 1


def _data_status_text() -> str:
        claims_df = st.session_state.get("claims_df")
        eob_df = st.session_state.get("parsed_eob_records")
        has_claims = claims_df is not None and not claims_df.empty
        eob_count = 0 if eob_df is None else len(eob_df)

        if has_claims and eob_count:
                return "EOB + claims data ready"
        if has_claims:
                return "Claims data loaded"
        if eob_count:
                return f"{eob_count} EOB{'s' if eob_count != 1 else ''} loaded"
        return "No data loaded"


def _render_header() -> None:
        status_text = _data_status_text()
        if not st.session_state.get("data_ready"):
                st.markdown(
                        f"""
                        <section class="landing-hero">
                            <div class="landing-mark" aria-hidden="true"><span>+</span><small>▥</small></div>
                            <div class="landing-hero-copy">
                                <h1>Healthcare Claims Analytics</h1>
                                <h2>Understand your healthcare spending — without decoding every EOB yourself.</h2>
                                <p>
                                    Upload your Explanation of Benefits or claims data to see where your healthcare dollars went,
                                    understand what your insurance paid, what you may owe, and how service costs compare with
                                    public Medicare averages for additional context.
                                </p>
                                <div class="trust-line">Your files are analyzed only for this session. Use de-identified data for this demonstration.</div>
                            </div>
                            <div class="product-status">{status_text}</div>
                        </section>
                        """,
                        unsafe_allow_html=True,
                )
                return

        st.markdown(
                f"""
                <section class="product-header">
                    <div class="product-mark">HC</div>
                    <div class="product-copy">
                        <h1>{APP_TITLE}</h1>
                        <p>{APP_SUBTITLE}</p>
                    </div>
                    <div class="product-status">{status_text}</div>
                </section>
                """,
                unsafe_allow_html=True,
        )


def _render_navigation() -> str:
    data_ready = bool(st.session_state.get("data_ready"))
    if not data_ready:
        return TAB_1

    options = [TAB_1, TAB_2, TAB_4, TAB_3, TAB_5]

    # Apply deferred tab navigation requests before rendering the widget.
    next_tab = st.session_state.get("next_active_tab")
    if next_tab in options:
        st.session_state["active_tab"] = next_tab
    st.session_state["next_active_tab"] = None

    if st.session_state.get("active_tab", TAB_1) not in options:
        st.session_state["active_tab"] = TAB_2 if data_ready else TAB_1

    selected_tab = st.radio(
        "Navigation",
        options=options,
        key="active_tab",
        format_func=lambda tab: NAV_LABELS[tab],
        horizontal=True,
        label_visibility="collapsed",
    )
    return str(selected_tab or st.session_state.get("active_tab", TAB_1))


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon=":material/analytics:", layout="wide")
    _load_local_css()
    _init_session_state()

    _render_header()

    if st.session_state.get("data_ready"):
        c1, c2 = st.columns([0.78, 0.22])
        with c2:
            if st.button(
                "Start over with new files",
                type="primary",
                icon=":material/refresh:",
                width="stretch",
                help="Clear this session and upload different EOBs or claims data.",
            ):
                _clear_analysis_state()
                st.rerun()

    selected_tab = _render_navigation()

    if selected_tab == TAB_1:
        render_tab_upload()
    elif selected_tab == TAB_2:
        render_tab_overview(
            st.session_state.get("claims_df"),
            st.session_state.get("parsed_eob_records"),
        )
    elif selected_tab == TAB_3:
        render_tab_spending_analysis(
            st.session_state.get("claims_df"),
            st.session_state.get("parsed_eob_records"),
        )
    elif selected_tab == TAB_4:
        render_tab_eob_explainer(
            st.session_state.get("claims_df"),
            st.session_state.get("parsed_eob_records"),
        )
    elif selected_tab == TAB_5:
        render_tab_cost_benchmark(
            st.session_state.get("claims_df"),
            st.session_state.get("cms_df"),
            st.session_state.get("parsed_eob_records"),
        )


if __name__ == "__main__":
    main()
