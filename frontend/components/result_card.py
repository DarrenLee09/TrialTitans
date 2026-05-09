"""Render a single statute result."""
from __future__ import annotations

import streamlit as st


def render(statute: dict) -> None:
    cite = f"{statute.get('jurisdiction')} {statute.get('code_name')} § {statute.get('section')}"
    title = statute.get("title") or ""
    with st.container(border=True):
        st.markdown(f"### {cite}  \n{title}")
        if statute.get("snippet"):
            st.markdown(statute["snippet"], unsafe_allow_html=True)
        elif statute.get("body"):
            st.markdown((statute["body"][:600] + "…") if len(statute["body"]) > 600 else statute["body"])
        if statute.get("source_url"):
            st.markdown(f"[Source]({statute['source_url']})")
