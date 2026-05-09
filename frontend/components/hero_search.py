"""Hero search row: input, jurisdiction, AI toggle, example chips."""
from __future__ import annotations

import streamlit as st

from db.seed import connect

EXAMPLE_QUERIES = [
    "CA Veh Code 22107",
    "rear-ended at a stop sign",
    "failure to yield at intersection",
]


def _jurisdictions() -> list[tuple[str, str]]:
    with connect() as conn:
        return [(r["code"], r["name"]) for r in conn.execute(
            "SELECT code, name FROM jurisdictions ORDER BY name"
        )]


def render() -> tuple[str, str | None, bool]:
    """Render hero. Returns (query, jurisdiction_code_or_none, use_ai)."""
    if "_chip_pending" in st.session_state:
        st.session_state["query"] = st.session_state.pop("_chip_pending")

    st.markdown('<div class="tt-hero-label">Search the record</div>', unsafe_allow_html=True)
    st.markdown('<div class="tt-hero-scope"></div>', unsafe_allow_html=True)

    cols = st.columns([5, 2, 1.4])
    with cols[0]:
        query = st.text_input(
            "Search",
            key="query",
            label_visibility="collapsed",
            placeholder="Citation, factor, or describe the accident…",
        )
    with cols[1]:
        juris_options = [("", "Any jurisdiction")] + _jurisdictions()
        jur_label = st.selectbox(
            "Jurisdiction",
            [name for _, name in juris_options],
            label_visibility="collapsed",
        )
        jurisdiction = next((code for code, name in juris_options if name == jur_label), "") or None
    with cols[2]:
        use_ai = st.toggle(
            "AI memo",
            value=st.session_state.get("use_ai", False),
            key="use_ai",
        )

    st.markdown('<div class="tt-chip-label">Try one</div>', unsafe_allow_html=True)
    st.markdown('<div class="tt-chip-row-marker"></div>', unsafe_allow_html=True)
    chip_cols = st.columns([0.65, 0.95, 1.05, 5])
    for i, eg in enumerate(EXAMPLE_QUERIES):
        with chip_cols[i]:
            if st.button(eg, key=f"chip-{i}"):
                st.session_state["_chip_pending"] = eg
                st.rerun()

    return query, jurisdiction, use_ai
