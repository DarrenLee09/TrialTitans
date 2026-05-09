"""Landing-state explainer: three retrieval modes."""
from __future__ import annotations

import streamlit as st

MODES = [
    ("1", "Search by citation", "Jump straight to a section when you already know the cite.", "CA Veh Code 22107"),
    ("2", "Search by factor", "Pull every statute that touches a contributing factor.", "failure to yield"),
    ("3", "Describe the accident", "Plain English works — we route to the right statutes.", "rear-ended at a stop sign"),
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
