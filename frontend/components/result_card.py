"""Render a single statute result.

Each card collapses the full statute body behind an expander so the user can
read the whole thing in context, and offers a one-click PI-focused AI summary
that's cached per-statute so re-renders don't re-charge the API.
"""
from __future__ import annotations

import html as _html
import os
import re

import streamlit as st


def _citation(s: dict) -> str:
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


_SECTION_RE = re.compile(r"§\s*([0-9][\w\.\-]*)")


def _linkify_inline_citations(text: str) -> str:
    """Wrap '§ 22107' style refs in styled pills so summaries surface their
    cited sections visibly. We don't try to scroll-jump (no anchor IDs at
    summary time); the pill itself is the in-text citation marker."""
    def repl(m: re.Match[str]) -> str:
        sec = _html.escape(m.group(1))
        return f'<span class="tt-cite-pill">§ {sec}</span>'
    return _SECTION_RE.sub(repl, text)


def _summarize_via_claude(statute: dict) -> str | None:
    """One-shot PI-focused summary of this statute. Returns plain text or None
    if no API key / API error."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        from anthropic import Anthropic
    except ImportError:
        return None

    client = Anthropic()
    body = (statute.get("body") or statute.get("full_text") or "")[:4000]
    if not body:
        return None
    cite = _citation(statute)
    title = statute.get("title") or ""

    prompt = (
        "You are a research assistant for a plaintiff-side personal-injury attorney. "
        "Summarize the statute below in 3-5 sentences. Focus on:\n"
        " - What conduct it requires or prohibits\n"
        " - When it applies (who, where, in what circumstances)\n"
        " - Civil liability implications a PI lawyer would care about\n"
        "Always cite the section inline as '§ <number>' when referencing rules. "
        "Do not invent details not in the text.\n\n"
        f"Citation: {cite}\n"
        f"Title: {title}\n"
        f"Body:\n{body}"
    )

    try:
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text if msg.content else None
    except Exception:
        return None


def _summary_cache_key(sid: object) -> str:
    return f"_tt_summary_{sid}"


def render(statute: dict) -> None:
    sid = statute.get("id") or f"live-{abs(hash(statute.get('citation',''))) & 0xffff:x}"
    cite = _html.escape(_citation(statute))
    title = _html.escape(statute.get("title") or "")
    excerpt = _excerpt(statute)
    factors_html = _factor_tags(statute)
    source_url = statute.get("source_url")
    source_html = (
        f'<a class="tt-card-source-link" href="{_html.escape(source_url)}" target="_blank" rel="noreferrer">View source ↗ {_html.escape(_source_domain(source_url))}</a>'
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
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)

    # Action row: pin / summarize / show full text — all stay attached to the card
    pinned_ids = {p["id"] for p in st.session_state.get("case_pinned", [])}
    is_pinned = sid in pinned_ids
    body_text = statute.get("body") or statute.get("full_text") or ""
    summary_key = _summary_cache_key(sid)
    cached_summary = st.session_state.get(summary_key)

    cols = st.columns([1.1, 1.6, 1.6, 4])
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
        sum_label = "✦ Re-summarize" if cached_summary else "✦ Summarize for PI"
        if st.button(sum_label, key=f"sum-{sid}"):
            with st.spinner("Drafting…"):
                summary = _summarize_via_claude(statute)
            st.session_state[summary_key] = summary or "Summary unavailable."
            st.rerun()
    with cols[2]:
        # Source link rendered as small action — keeps card cleaner
        if source_url:
            st.markdown(source_html, unsafe_allow_html=True)

    # Inline AI summary (if generated)
    if cached_summary:
        body_html = _linkify_inline_citations(_html.escape(cached_summary)).replace("\n\n", "</p><p>").replace("\n", "<br>")
        if not body_html.startswith("<p>"):
            body_html = f"<p>{body_html}</p>"
        st.markdown(
            f'<div class="tt-card-summary">'
            f'<div class="tt-card-summary-eyebrow">AI summary · for PI counsel</div>'
            f'<div class="tt-card-summary-body">{body_html}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Collapsible full-text — shows the entire statute body in context
    if body_text:
        with st.expander("Read full statute"):
            st.markdown(body_text)
