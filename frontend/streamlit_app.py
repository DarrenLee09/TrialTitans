"""TrialTitans — Streamlit UI for the Legal Statute Harvester."""
from __future__ import annotations

import sys
from pathlib import Path

# Make repo root importable when running `streamlit run frontend/streamlit_app.py`.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from ai import answer_generator
from frontend.components import case_workspace, result_card, search_bar
from retrieval import query_router, reranker

st.set_page_config(page_title="TrialTitans — Statute Search", layout="wide")
st.title("TrialTitans — Legal Statute Search")

query, jurisdiction, use_ai = search_bar.render()

if query:
    routed = query_router.route(query, jurisdiction=jurisdiction or None, limit=20)
    results = routed["results"]

    if use_ai and routed["kind"] == "fts":
        results = reranker.rerank(query, results, top_k=8)

    st.caption(f"Route: **{routed['kind']}**  ·  {len(results)} result(s)")

    left, right = st.columns([2, 1])
    with left:
        for s in results:
            result_card.render(s)

    with right:
        if use_ai and results:
            st.subheader("AI summary")
            with st.spinner("Drafting attorney memo…"):
                memo = answer_generator.answer(query, results, jurisdiction=jurisdiction)
            st.markdown(memo)

        case_workspace.render(results)
