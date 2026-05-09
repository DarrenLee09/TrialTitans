"""Search bar + jurisdiction filter."""
from __future__ import annotations

import streamlit as st

from db.seed import connect


def _jurisdictions() -> list[tuple[str, str]]:
    with connect() as conn:
        return [(r["code"], r["name"]) for r in conn.execute("SELECT code, name FROM jurisdictions ORDER BY name")]


def render() -> tuple[str, str | None, bool]:
    cols = st.columns([4, 1, 1])
    query = cols[0].text_input(
        "Search by citation, factor, or accident description",
        placeholder="e.g. 'CA Veh Code 22107' or 'failure to yield' or 'rear-ended at a stop sign'",
    )
    juris_options = [("", "Any jurisdiction")] + _jurisdictions()
    jur_label = cols[1].selectbox("Jurisdiction", [name for _, name in juris_options])
    jurisdiction = next((code for code, name in juris_options if name == jur_label), "") or None
    use_ai = cols[2].toggle("AI rerank + memo", value=False)
    return query, jurisdiction, use_ai
