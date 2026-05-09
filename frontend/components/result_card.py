"""Render a single statute result as a magazine-TOC entry."""
from __future__ import annotations

import html as _html

import streamlit as st


def _citation(s: dict) -> str:
    # Prefer the canonical citation stored on the row — written by the scraper
    # with the proper code prefix. Fall back to assembling from joined columns.
    if s.get("citation"):
        return s["citation"]
    return f"{s.get('jurisdiction', '?')} {s.get('code_name', '?')} § {s.get('section', '?')}"


def _factor_label(f: object) -> str:
    if isinstance(f, dict):
        return f.get("label") or f.get("code") or ""
    return str(f)


def _factor_tags(s: dict) -> str:
    factors = s.get("factors") or []
    if not factors:
        return ""
    pills = "".join(
        f'<span class="tt-tag">{_html.escape(_factor_label(f))}</span>' for f in factors[:4]
    )
    return f'<div class="tt-tags">{pills}</div>'


def _excerpt(s: dict) -> str:
    if s.get("snippet"):
        return s["snippet"]
    body = s.get("body") or s.get("full_text") or ""
    return _html.escape(body[:420] + ("…" if len(body) > 420 else ""))


def _source_domain(url: str) -> str:
    from urllib.parse import urlparse
    try:
        return urlparse(url).netloc or url
    except Exception:
        return url


def _live_badge(statute: dict) -> str:
    if not statute.get("is_live_fetch"):
        return ""
    domain = _html.escape(_source_domain(statute.get("source_url") or ""))
    return f'<span class="tt-live-badge"><span class="tt-live-dot"></span>Live · {domain}</span>'


def render(statute: dict) -> None:
    sid = statute.get("id") or f"live-{abs(hash(statute.get('citation',''))) & 0xffff:x}"
    cite = _html.escape(_citation(statute))
    title = _html.escape(statute.get("title") or "")
    excerpt = _excerpt(statute)
    factors_html = _factor_tags(statute)
    source_url = statute.get("source_url")
    source_html = (
        f'<div class="tt-card-source"><a href="{_html.escape(source_url)}" target="_blank" rel="noreferrer">View source <span aria-hidden="true">→</span></a></div>'
        if source_url else ""
    )
    live_html = _live_badge(statute)
    explanation = (statute.get("explanation") or "").strip()
    explanation_html = (
        f'<div class="tt-card-rationale"><strong>Why this matters:</strong> {_html.escape(explanation)}</div>'
        if explanation else ""
    )

    card_html = (
        f'<div class="tt-card" id="statute-{sid}">'
        f'<div class="tt-card-meta">'
        f'<span class="tt-citation">{cite}</span>'
        f'{live_html}'
        f'<span class="tt-meta-spacer"></span>'
        f'</div>'
        f'<h3 class="tt-card-title">{title}</h3>'
        f'<div class="tt-card-body">{excerpt}</div>'
        f'{explanation_html}'
        f'{factors_html}'
        f'{source_html}'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)

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
