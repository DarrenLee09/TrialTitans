"""Top bar: logo, wordmark, tagline, build label."""
from __future__ import annotations

from datetime import date

import streamlit as st


def render() -> None:
    today = date.today().strftime("%b %d, %Y")
    html = (
        '<div class="tt-topbar">'
        '<div class="tt-topbar-left">'
        '<span class="tt-logo">T&amp;T</span>'
        '<span class="tt-wordmark">Trial<span class="tt-amp">&amp;</span>Titans</span>'
        '<span class="tt-tagline">Research desk for accident litigation</span>'
        '</div>'
        f'<div class="tt-issue">{today}</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
