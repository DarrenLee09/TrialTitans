"""Hero search row: input, jurisdiction, AI toggle, example chips."""
from __future__ import annotations

import html as _html
from urllib.parse import quote

import streamlit as st

from db.seed import connect

EXAMPLE_QUERIES = [
    ("01", "CA Veh Code 22107"),
    ("02", "rear-ended at a stop sign"),
    ("03", "failure to yield at intersection"),
]


def _jurisdictions() -> list[tuple[str, str]]:
    with connect() as conn:
        return [(r["code"], r["name"]) for r in conn.execute(
            "SELECT code, name FROM jurisdictions ORDER BY name"
        )]


def _consume_chip_param() -> None:
    """If the URL has ?q=..., apply it to the search box and clean the URL."""
    q = st.query_params.get("q")
    if q:
        st.session_state["_chip_pending"] = q
        try:
            del st.query_params["q"]
        except KeyError:
            pass


def render() -> tuple[str, str | None, bool]:
    """Render hero. Returns (query, jurisdiction_code_or_none, use_ai)."""
    _consume_chip_param()

    if "_chip_pending" in st.session_state:
        st.session_state["query"] = st.session_state.pop("_chip_pending")

    st.markdown('<div class="tt-hero-label">Search statutes</div>', unsafe_allow_html=True)

    cols = st.columns([5, 2, 1.4])
    with cols[0]:
        query = st.text_input(
            "Search",
            key="query",
            label_visibility="collapsed",
            placeholder="Search by citation, factor, or describe the accident…",
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

    chips_html = "".join(
        f'<a class="tt-chip" href="?q={quote(eg)}"><span class="tt-chip-eg-mark">{num}</span>{_html.escape(eg)}</a>'
        for num, eg in EXAMPLE_QUERIES
    )
    st.markdown('<div class="tt-chip-label">Try a sample query</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="tt-chip-row">{chips_html}</div>', unsafe_allow_html=True)

    return query, jurisdiction, use_ai
