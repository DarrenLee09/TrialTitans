"""Side-panel workspace for collecting statutes into a working case file."""
from __future__ import annotations

import streamlit as st


def render(results: list[dict]) -> None:
    st.subheader("Case workspace")
    if "case_pinned" not in st.session_state:
        st.session_state.case_pinned = []

    for s in results:
        cite = s.get("citation") or f"{s.get('jurisdiction')} §{s.get('section')}"
        if st.button(f"Pin {cite}", key=f"pin-{s['id']}"):
            if s["id"] not in {p["id"] for p in st.session_state.case_pinned}:
                st.session_state.case_pinned.append(s)

    if st.session_state.case_pinned:
        st.markdown("**Pinned statutes**")
        for s in st.session_state.case_pinned:
            cite = s.get("citation") or f"{s.get('jurisdiction')} §{s.get('section')}"
            st.markdown(f"- {cite} — {s.get('title') or ''}")
        if st.button("Clear workspace"):
            st.session_state.case_pinned = []
    else:
        st.caption("Pin statutes from the results to build a working case file.")
