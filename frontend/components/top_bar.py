"""Editorial masthead: wordmark, tagline, issue line."""
from __future__ import annotations

from datetime import date

import streamlit as st


def render() -> None:
    today = date.today().strftime("%B %d, %Y").upper()
    st.markdown(
        f"""
        <div class="tt-topbar">
          <div class="tt-topbar-left">
            <span class="tt-wordmark">Trial<span class="tt-amp">&amp;</span>Titans</span>
            <span class="tt-tagline">A research desk for accident litigation</span>
          </div>
          <div class="tt-issue">Vol. I · {today}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
