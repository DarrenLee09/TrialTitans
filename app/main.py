"""TrialTitans — Streamlit entrypoint."""
from __future__ import annotations

import sys
from pathlib import Path

# Make repo root importable when launched as `streamlit run app/main.py`.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from ai import answer_generator
from app import config
from app.components import case_workspace, coverage_panel, result_card, search_bar
from retrieval import reranker

st.set_page_config(page_title="TrialTitans — Statute Search", layout="wide")
st.title("TrialTitans — Legal Statute Search")
st.caption(
    "Citation, contributing factor, and natural-language search across multi-state vehicle codes. "
    f"Model: `{config.CLAUDE_MODEL}` · "
    f"AI features: {'on' if config.AI_AVAILABLE else 'off (set ANTHROPIC_API_KEY)'}"
)

coverage_panel.render()

ai_toggle = st.sidebar.toggle(
    "AI rerank + memo",
    value=False,
    disabled=not config.AI_AVAILABLE,
    help="Requires ANTHROPIC_API_KEY in .env",
)

outcome = search_bar.render()

if outcome is None:
    st.info("Pick a search mode above to get started.")
    st.stop()

results = outcome.results
if not results:
    st.warning("No matches.")
    st.stop()

# AI rerank only makes sense for the natural-language tab.
if ai_toggle and outcome.kind == "nl":
    results = reranker.rerank(outcome.query, results, top_k=8)

st.caption(f"Mode: **{outcome.kind}** · {len(results)} result(s)")

left, right = st.columns([2, 1])
with left:
    for s in results:
        result_card.render(s)

with right:
    if ai_toggle and outcome.kind == "nl":
        st.subheader("AI memo")
        with st.spinner("Drafting attorney memo…"):
            memo = answer_generator.answer(
                outcome.query, results, jurisdiction=outcome.jurisdiction
            )
        st.markdown(memo)

    case_workspace.render(results)
