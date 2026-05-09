"""TrialTitans — Streamlit UI for the Legal Statute Harvester."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from frontend import styles
from frontend.components import (
    ai_memo_rail,
    case_file_sidebar,
    case_file_view,
    empty_state,
    hero_search,
    loading_state,
    result_card,
    top_bar,
)
from organizer import fill_case as organizer
from retrieval import query_router, reranker


def _run() -> None:
    st.set_page_config(
        page_title="Trial & Titans — Legal Research Desk",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    styles.inject()

    if "case_pinned" not in st.session_state:
        st.session_state.case_pinned = []

    case_file_sidebar.render()

    top_bar.render()

    query, jurisdiction, use_ai, mode = hero_search.render()

    if not query:
        empty_state.render()
        st.stop()

    skeleton_slot = st.empty()
    with skeleton_slot.container():
        loading_state.render()

    routed = query_router.route(query, jurisdiction=jurisdiction or None, limit=20)
    results = routed["results"]

    if mode == "search" and use_ai and routed["kind"] == "fts" and results:
        results = reranker.rerank(query, results, top_k=8)

    skeleton_slot.empty()

    st.session_state["last_results"] = results

    route_html = (
        '<div class="tt-route-caption">'
        f'<span>route &middot; <span class="tt-route-kind">{routed["kind"]}</span></span>'
        f'<span class="tt-route-count">{len(results):02d} result(s)</span>'
        '</div>'
    )
    st.markdown(route_html, unsafe_allow_html=True)

    if mode == "case_file":
        if not results:
            st.warning(
                "No relevant statutes retrieved — refine the case description or "
                "broaden the jurisdiction filter."
            )
            st.stop()
        with st.spinner("Filling case file…"):
            filled = organizer.fill_case(query, results, jurisdiction=jurisdiction)
        case_file_view.render(filled, query)
        return

    if not results:
        no_results_html = (
            '<div class="tt-no-results">'
            '<h3>Nothing on the record.</h3>'
            '<p>Try a different phrasing &mdash; a citation like <em>CA Veh Code 22107</em>, '
            'a factor like <em>failure to yield</em>, or describe the accident in plain English.</p>'
            '</div>'
        )
        st.markdown(no_results_html, unsafe_allow_html=True)
        st.stop()

    if use_ai:
        main_col, rail_col = st.columns([3, 2], gap="large")
        with main_col:
            for s in results:
                result_card.render(s)
        with rail_col:
            ai_memo_rail.render(query, results, jurisdiction)
    else:
        for s in results:
            result_card.render(s)


if __name__ == "__main__":
    _run()
