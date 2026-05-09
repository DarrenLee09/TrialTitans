"""Skeleton entries shown while results compute."""
from __future__ import annotations

import streamlit as st


def render(count: int = 3) -> None:
    skeleton = (
        '<div class="tt-skel">'
        '<div class="tt-skel-bar" style="width: 18%; height: 10px;"></div>'
        '<div class="tt-skel-bar" style="width: 70%; height: 22px; margin-top: 14px;"></div>'
        '<div class="tt-skel-bar" style="width: 100%; margin-top: 14px;"></div>'
        '<div class="tt-skel-bar" style="width: 92%;"></div>'
        '<div class="tt-skel-bar" style="width: 35%; margin-top: 12px;"></div>'
        '</div>'
    )
    st.markdown(skeleton * count, unsafe_allow_html=True)
