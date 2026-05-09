"""Right rail: AI-generated attorney memo with editorial drop-cap."""
from __future__ import annotations

import html as _html
import os
import re

import streamlit as st

from ai import answer_generator

_SECTION_RE = re.compile(r"§\s*([0-9.\-]+)")


def _linkify_citations(memo: str, results: list[dict]) -> str:
    section_to_id: dict[str, object] = {}
    for s in results:
        sec = str(s.get("section") or "").strip()
        if sec and sec not in section_to_id:
            section_to_id[sec] = s.get("id")

    def repl(m: re.Match[str]) -> str:
        sec = m.group(1)
        sid = section_to_id.get(sec)
        if sid is None:
            return m.group(0)
        return f'<a class="tt-cite-pill" href="#statute-{sid}">§ {sec}</a>'

    return _SECTION_RE.sub(repl, memo)


def render(query: str, results: list[dict], jurisdiction: str | None) -> None:
    if not results:
        return

    if not os.environ.get("ANTHROPIC_API_KEY"):
        fallback_html = (
            '<div class="tt-memo">'
            '<div class="tt-memo-eyebrow">Editorial &middot; Memo</div>'
            '<h2>Memorandum</h2>'
            '<div class="tt-memo-byline">A research note for the attorney of record.</div>'
            '<div class="tt-memo-fallback">Set <code>ANTHROPIC_API_KEY</code> in the environment to enable the AI memo.</div>'
            '</div>'
        )
        st.markdown(fallback_html, unsafe_allow_html=True)
        return

    cache_key = ("memo", query, jurisdiction, tuple(s.get("id") for s in results))
    if st.session_state.get("_memo_cache_key") != cache_key:
        with st.spinner("Drafting…"):
            memo_text = answer_generator.answer(query, results, jurisdiction=jurisdiction)
        st.session_state["last_memo"] = memo_text
        st.session_state["_memo_cache_key"] = cache_key
    else:
        memo_text = st.session_state.get("last_memo", "")

    body_html = _linkify_citations(memo_text, results).replace("\n\n", "</p><p>").replace("\n", "<br>")
    if not body_html.startswith("<p>"):
        body_html = f"<p>{body_html}</p>"

    juris_label = (jurisdiction or "Any jurisdiction").upper()
    safe_query = _html.escape(query)
    memo_html = (
        '<div class="tt-memo">'
        '<div class="tt-memo-eyebrow">Answer &middot; Attorney Memo</div>'
        '<h2>Memorandum</h2>'
        f'<div class="tt-memo-byline">Re: <em>{safe_query}</em> &middot; {juris_label} &middot; sources cited inline</div>'
        f'<div class="tt-memo-body">{body_html}</div>'
        '</div>'
    )
    st.markdown(memo_html, unsafe_allow_html=True)
