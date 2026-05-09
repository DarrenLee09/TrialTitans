"""Landing-state explainer: three retrieval modes."""
from __future__ import annotations

import streamlit as st

MODES = [
    ("01", "By citation", "Pinpoint a specific section when you already know the cite.", "CA Veh Code 22107"),
    ("02", "By factor", "Surface statutes that touch a contributing factor.", "failure to yield"),
    ("03", "By description", "Describe the accident in plain English; we route the search.", "rear-ended at a stop sign"),
]


def render() -> None:
    cards = "".join(
        f'<div class="tt-mode-card">'
        f'<div class="tt-mode-num">{num}</div>'
        f'<h4>{label}</h4>'
        f'<p>{desc}</p>'
        f'<span class="tt-mode-eg">{eg}</span>'
        f'</div>'
        for num, label, desc, eg in MODES
    )
    st.markdown(f'<div class="tt-explainer">{cards}</div>', unsafe_allow_html=True)
