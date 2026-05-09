"""Render a single statute result as a magazine-TOC entry."""
from __future__ import annotations

import html as _html

import streamlit as st


def _citation(s: dict) -> str:
    return f"{s.get('jurisdiction', '?')} {s.get('code_name', '?')} § {s.get('section', '?')}"


def _factor_tags(s: dict) -> str:
    factors = s.get("factors") or []
    if not factors:
        return ""
    pills = "".join(
        f'<span class="tt-tag">{_html.escape(str(f))}</span>' for f in factors[:4]
    )
    return f'<div class="tt-tags">{pills}</div>'


def _excerpt(s: dict) -> str:
    if s.get("snippet"):
        return s["snippet"]
    body = s.get("body") or s.get("full_text") or ""
    return _html.escape(body[:420] + ("…" if len(body) > 420 else ""))


def render(statute: dict) -> None:
    sid = statute.get("id", "x")
    cite = _html.escape(_citation(statute))
    title = _html.escape(statute.get("title") or "")
    excerpt = _excerpt(statute)
    factors_html = _factor_tags(statute)
    source_url = statute.get("source_url")
    source_html = (
        f'<div class="tt-card-source"><a href="{_html.escape(source_url)}" target="_blank" rel="noreferrer">View source ↗</a></div>'
        if source_url else ""
    )

    st.markdown(
        f"""
        <div class="tt-card" id="statute-{sid}">
          <div class="tt-card-meta">
            <span class="tt-citation">{cite}</span>
            <span class="tt-meta-spacer"></span>
          </div>
          <h3 class="tt-card-title">{title}</h3>
          <div class="tt-card-body">{excerpt}</div>
          {factors_html}
          {source_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    pinned_ids = {p["id"] for p in st.session_state.get("case_pinned", [])}
    is_pinned = sid in pinned_ids

    cols = st.columns([1.1, 1.6, 5])
    with cols[0]:
        label = "★ Pinned" if is_pinned else "+ Pin to file"
        if st.button(label, key=f"pin-{sid}"):
            if is_pinned:
                st.session_state.case_pinned = [
                    p for p in st.session_state.case_pinned if p["id"] != sid
                ]
            else:
                st.session_state.case_pinned.append(statute)
            st.rerun()
    with cols[1]:
        body_text = statute.get("body") or statute.get("full_text")
        if body_text:
            with st.expander("Read full text"):
                st.markdown(body_text)
