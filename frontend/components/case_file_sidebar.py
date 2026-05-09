"""Left sidebar: pinned statutes, count, export."""
from __future__ import annotations

import html as _html

import streamlit as st


def _citation(s: dict) -> str:
    return f"{s.get('jurisdiction', '?')} {s.get('code_name', '?')} § {s.get('section', '?')}"


def _build_markdown(pinned: list[dict], memo: str | None) -> str:
    lines = ["# Case File", ""]
    for s in pinned:
        lines.append(f"## {_citation(s)} — {s.get('title') or ''}")
        if s.get("source_url"):
            lines.append(f"[Source]({s['source_url']})")
        lines.append("")
        body = s.get("body") or ""
        lines.append(body[:1500] + ("…" if len(body) > 1500 else ""))
        lines.append("")
    if memo:
        lines.append("---")
        lines.append("# AI memo")
        lines.append("")
        lines.append(memo)
    return "\n".join(lines)


def render() -> None:
    pinned: list[dict] = st.session_state.get("case_pinned", [])
    memo = st.session_state.get("last_memo")

    with st.sidebar:
        st.markdown(
            f"""
            <div class="tt-sidebar-eyebrow">The Working File</div>
            <div class="tt-sidebar-title">Case File <span class="tt-badge">{len(pinned):02d}</span></div>
            <div class="tt-sidebar-rule"></div>
            """,
            unsafe_allow_html=True,
        )

        if not pinned:
            st.markdown(
                '<div class="tt-sidebar-empty">No statutes pinned yet. Pin from the results to begin assembling a case.</div>',
                unsafe_allow_html=True,
            )
            return

        for s in pinned:
            cite = _html.escape(_citation(s))
            title = _html.escape((s.get("title") or "")[:80])
            sid = s.get("id", "x")
            st.markdown(
                f"""
                <div class="tt-pinned-item">
                  <div class="tt-pinned-cite">{cite}</div>
                  <div class="tt-pinned-title">{title}</div>
                </div>
                <div class="tt-unpin-marker"></div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Remove", key=f"unpin-{sid}"):
                st.session_state.case_pinned = [
                    p for p in pinned if p["id"] != sid
                ]
                st.rerun()

        st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
        st.download_button(
            "Export memo",
            data=_build_markdown(pinned, memo),
            file_name="case_file.md",
            mime="text/markdown",
            use_container_width=True,
        )
        if st.button("Clear case file", use_container_width=True):
            st.session_state.case_pinned = []
            st.rerun()
