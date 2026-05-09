"""Render a single statute result as a card."""
from __future__ import annotations

import hashlib

import streamlit as st

# Stable colors per factor code so the same factor is always the same shade.
_PALETTE = [
    "#2563eb",  # blue
    "#dc2626",  # red
    "#16a34a",  # green
    "#9333ea",  # purple
    "#ea580c",  # orange
    "#0891b2",  # cyan
    "#ca8a04",  # amber
    "#db2777",  # pink
    "#475569",  # slate
]


def _color_for(code: str) -> str:
    h = int(hashlib.md5(code.encode()).hexdigest(), 16)
    return _PALETTE[h % len(_PALETTE)]


def _badges(factors: list[dict]) -> str:
    parts = []
    for f in factors:
        color = _color_for(f["code"])
        conf = f.get("confidence")
        conf_txt = f" · {conf:.2f}" if isinstance(conf, (int, float)) else ""
        parts.append(
            f"<span style='background:{color};color:white;padding:2px 8px;"
            f"border-radius:8px;font-size:0.8rem;margin-right:4px;display:inline-block;"
            f"margin-bottom:4px;'>{f['label']}{conf_txt}</span>"
        )
    return "".join(parts)


def _verified_pill(is_verified: int | bool | None) -> str:
    if is_verified:
        return "<span style='color:#16a34a;font-size:0.85rem;'>● verified URL</span>"
    return "<span style='color:#9ca3af;font-size:0.85rem;'>○ unverified</span>"


def render(statute: dict) -> None:
    citation = statute.get("citation") or (
        f"{statute.get('jurisdiction')} §{statute.get('section')}"
    )
    title = statute.get("title") or ""
    factors = statute.get("factors") or []
    full_text = statute.get("full_text") or ""
    snippet = statute.get("snippet")
    source_url = statute.get("source_url")

    with st.container(border=True):
        header_l, header_r = st.columns([4, 1])
        header_l.markdown(f"### {citation}")
        header_r.markdown(_verified_pill(statute.get("is_verified")), unsafe_allow_html=True)

        if title:
            st.markdown(f"**{title}**")
        if statute.get("statute_title"):
            st.caption(statute["statute_title"])

        if factors:
            st.markdown(_badges(factors), unsafe_allow_html=True)

        # Snippet for FTS results, otherwise expandable full text.
        if snippet:
            st.markdown(snippet, unsafe_allow_html=True)
            with st.expander("Show full statute text"):
                st.markdown(full_text)
        else:
            preview = full_text[:300] + ("…" if len(full_text) > 300 else "")
            st.markdown(preview)
            if len(full_text) > 300:
                with st.expander("Show full statute text"):
                    st.markdown(full_text)

        if source_url:
            st.markdown(f"[Source ↗]({source_url})")
