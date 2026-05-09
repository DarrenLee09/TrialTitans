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


MODES = [
    ("search", "Search statutes"),
    ("case_file", "Build case file"),
]


def render() -> tuple[str, str | None, bool, str]:
    """Render hero. Returns (query, jurisdiction_code_or_none, use_ai, mode)."""
    _consume_chip_param()

    if "_chip_pending" in st.session_state:
        st.session_state["query"] = st.session_state.pop("_chip_pending")

    mode_label = st.radio(
        "Mode",
        [label for _, label in MODES],
        horizontal=True,
        label_visibility="collapsed",
        key="mode_label",
    )
    mode = next((m for m, label in MODES if label == mode_label), "search")

    hero_label = (
        "Search the record" if mode == "search"
        else "Describe the case — we'll build the file"
    )
    st.markdown(f'<div class="tt-hero-label">{hero_label}</div>', unsafe_allow_html=True)

    placeholder = (
        "Citation, factor, or describe the accident…" if mode == "search"
        else "Describe the accident, client role, injuries, treatment, coverage…"
    )

    if mode == "case_file":
        cols = st.columns([5, 2])
    else:
        cols = st.columns([5, 2, 1.4])

    with cols[0]:
        query = st.text_input(
            "Search",
            key="query",
            label_visibility="collapsed",
            placeholder=placeholder,
        )
    with cols[1]:
        juris_options = [("", "Any jurisdiction")] + _jurisdictions()
        jur_label = st.selectbox(
            "Jurisdiction",
            [name for _, name in juris_options],
            label_visibility="collapsed",
        )
        jurisdiction = next((code for code, name in juris_options if name == jur_label), "") or None

    if mode == "case_file":
        use_ai = True  # case-file mode always uses Claude
    else:
        with cols[2]:
            use_ai = st.toggle(
                "AI memo",
                value=st.session_state.get("use_ai", False),
                key="use_ai",
            )

    if mode == "search":
        chips_html = "".join(
            f'<a class="tt-chip" href="?q={quote(eg)}"><span class="tt-chip-eg-mark">{num}</span>{_html.escape(eg)}</a>'
            for num, eg in EXAMPLE_QUERIES
        )
        st.markdown('<div class="tt-chip-label">Try one</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="tt-chip-row">{chips_html}</div>', unsafe_allow_html=True)

    return query, jurisdiction, use_ai, mode
