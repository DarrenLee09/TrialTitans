"""Render the Organizer's filled case file: summary + filled template + collapsible
relevant statutes + gap report."""
from __future__ import annotations

import html as _html

import streamlit as st


_BUCKET_LABELS = {
    "liability": "Liability",
    "damages": "Damages",
    "coverage": "Coverage",
    "credibility": "Credibility",
}

_TIER_DOTS = {1: "●●●●", 2: "●●●○", 3: "●●○○", 4: "●○○○"}


def render(filled: dict, query: str) -> None:
    """filled is the dict returned by organizer.fill_case."""
    if not filled.get("used_ai"):
        st.warning(
            "Organizer is in offline mode — set `ANTHROPIC_API_KEY` to populate "
            "the template from the case description and harvested statutes."
        )

    summary = filled.get("summary") or "(no summary)"
    st.markdown(
        f'<div class="tt-case-summary"><h3>Case file — at a glance</h3>'
        f'<p>{_html.escape(summary)}</p></div>',
        unsafe_allow_html=True,
    )

    statutes = filled.get("statutes_used") or []
    if statutes:
        st.markdown(
            f'<div class="tt-section-label">Relevant statutes ({len(statutes)})</div>',
            unsafe_allow_html=True,
        )
        for s in statutes:
            _render_statute_expander(s)

    st.markdown(
        '<div class="tt-section-label">Filled doctrine template</div>',
        unsafe_allow_html=True,
    )
    st.markdown(filled.get("filled_markdown") or "(empty)")

    gaps = filled.get("gap_report") or []
    if gaps:
        st.markdown(
            f'<div class="tt-section-label">Gap report ({len(gaps)} open)</div>',
            unsafe_allow_html=True,
        )
        _render_gap_table(gaps)


def _render_statute_expander(s: dict) -> None:
    cite = s.get("citation") or (
        f"{s.get('jurisdiction', '?')} {s.get('code_name', '?')} § {s.get('section', '?')}"
    )
    title = s.get("title") or ""
    header = f"{cite}" + (f" — {title}" if title else "")
    with st.expander(header):
        url = s.get("source_url")
        if url:
            st.markdown(f"[View source ↗]({url})")
        body = s.get("body") or s.get("full_text") or s.get("snippet") or ""
        if body:
            st.markdown(body)


def _render_gap_table(gaps: list[dict]) -> None:
    rows = []
    for g in gaps:
        bucket = _BUCKET_LABELS.get(g.get("bucket", ""), g.get("bucket", ""))
        tier = g.get("leverage_tier")
        tier_str = f"{tier} {_TIER_DOTS.get(tier, '')}" if tier else "—"
        rows.append({
            "Bucket": bucket,
            "Field": g.get("field", ""),
            "Tier": tier_str,
            "Closeable": g.get("closeable", ""),
            "Closing action": g.get("closing_action", ""),
        })
    st.dataframe(rows, hide_index=True, use_container_width=True)
