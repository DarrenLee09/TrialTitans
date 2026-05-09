# Frontend Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the TrialTitans Streamlit frontend so it looks like a focused legal-research product (not a generic Streamlit demo) for hackathon judging.

**Architecture:** Stay on Streamlit. Add a custom theme via `.streamlit/config.toml` plus a one-shot `<style>` block injected from `frontend/styles.py`. Replace the old components with a top bar, hero search, redesigned result cards, a left "Case File" sidebar, and a right AI memo rail. No backend / retrieval / AI changes.

**Tech Stack:** Streamlit, custom HTML/CSS injection (`st.markdown(unsafe_allow_html=True)`), Google Fonts (Source Serif 4, Inter, JetBrains Mono).

**Commit policy:** Per user feedback, do NOT commit between tasks. Only the final task in this plan creates a commit covering the entire redesign.

**Reference spec:** `docs/superpowers/specs/2026-05-09-frontend-redesign-design.md`

---

## File Structure

After this plan:

```
frontend/
  streamlit_app.py            # rewritten — thin orchestrator
  styles.py                   # NEW — CSS + font injection
  components/
    __init__.py               # unchanged
    top_bar.py                # NEW
    hero_search.py            # NEW
    result_card.py            # rewritten
    case_file_sidebar.py      # NEW
    ai_memo_rail.py           # NEW
    empty_state.py            # NEW
    loading_state.py          # NEW
    search_bar.py             # DELETED
    case_workspace.py         # DELETED
.streamlit/
  config.toml                 # NEW — theme primitives
tests/
  test_frontend_smoke.py      # NEW — import + render smoke test
```

Rationale: each file owns one piece of the UI, all under 100 lines. Easy to reason about and edit independently.

---

## Task 1: Streamlit theme config

**Files:**
- Create: `.streamlit/config.toml`

- [ ] **Step 1: Create the theme config**

Write `.streamlit/config.toml`:

```toml
[theme]
base = "dark"
primaryColor = "#7A1F2B"
backgroundColor = "#0E1116"
secondaryBackgroundColor = "#161A22"
textColor = "#E8E4D9"
font = "sans serif"

[server]
headless = true
runOnSave = true

[browser]
gatherUsageStats = false
```

- [ ] **Step 2: Verify file exists**

Run: `ls -la .streamlit/config.toml`
Expected: file exists with non-zero size.

---

## Task 2: Style injector module

**Files:**
- Create: `frontend/styles.py`

This module owns ALL custom CSS for the app. Called once from `streamlit_app.py`. It loads Google Fonts and styles every custom element (cards, chips, sidebar, citation pills, skeletons, hero input, scroll anchors).

- [ ] **Step 1: Create the styles module**

Write `frontend/styles.py`:

```python
"""One-shot CSS + font injection for the TrialTitans frontend."""
from __future__ import annotations

import streamlit as st

_INJECTED_KEY = "_tt_styles_injected"

_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500&family=Source+Serif+4:wght@500;600;700&display=swap" rel="stylesheet">

<style>
:root {
  --tt-bg: #0E1116;
  --tt-surface: #161A22;
  --tt-card: #F6F1E7;
  --tt-ink: #161A22;
  --tt-ink-muted: #6B7280;
  --tt-ink-on-dark: #E8E4D9;
  --tt-accent: #7A1F2B;
  --tt-hairline: rgba(0,0,0,0.08);
  --tt-radius: 12px;
}

html, body, [class*="css"] {
  font-family: 'Inter', system-ui, sans-serif;
}

h1, h2, h3, .tt-serif {
  font-family: 'Source Serif 4', Georgia, serif;
  letter-spacing: -0.01em;
}

/* Hide Streamlit chrome we don't want */
#MainMenu, footer, header[data-testid="stHeader"] { display: none; }

/* Reduce default top padding so the top bar sits flush */
section.main > div.block-container { padding-top: 1.25rem; padding-bottom: 4rem; max-width: 1400px; }

/* Top bar */
.tt-topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 4px 20px; border-bottom: 1px solid rgba(255,255,255,0.06);
  margin-bottom: 24px;
}
.tt-wordmark {
  font-family: 'Source Serif 4', serif; font-weight: 700; font-size: 22px;
  letter-spacing: 0.02em; color: var(--tt-ink-on-dark);
}
.tt-wordmark .tt-dot { color: var(--tt-accent); }
.tt-tagline { color: var(--tt-ink-muted); font-size: 13px; margin-left: 16px; }

/* Hero search input */
.stTextInput > div > div > input {
  font-size: 17px !important;
  height: 56px !important;
  background: var(--tt-card) !important;
  color: var(--tt-ink) !important;
  border-radius: var(--tt-radius) !important;
  border: 1px solid var(--tt-hairline) !important;
  padding: 0 18px !important;
}
.stTextInput > div > div > input:focus {
  outline: 2px solid var(--tt-accent) !important;
  outline-offset: 2px !important;
}

/* Example chips (rendered via st.button) */
.tt-chip-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
.tt-chip-row .stButton > button {
  background: rgba(246,241,231,0.08) !important;
  color: var(--tt-ink-on-dark) !important;
  border: 1px solid rgba(246,241,231,0.18) !important;
  border-radius: 999px !important;
  padding: 6px 14px !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  height: auto !important;
  min-height: 0 !important;
  transition: background 150ms ease-out, border-color 150ms ease-out;
}
.tt-chip-row .stButton > button:hover {
  background: rgba(246,241,231,0.14) !important;
  border-color: var(--tt-accent) !important;
  color: var(--tt-ink-on-dark) !important;
}

/* Result card */
.tt-card {
  background: var(--tt-card);
  color: var(--tt-ink);
  border-radius: var(--tt-radius);
  padding: 22px 24px;
  margin-bottom: 14px;
  border: 1px solid var(--tt-hairline);
  scroll-margin-top: 96px;
}
.tt-card-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 8px; }
.tt-citation {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px; font-weight: 500;
  color: var(--tt-accent);
  background: rgba(122,31,43,0.08);
  border: 1px solid rgba(122,31,43,0.2);
  border-radius: 999px;
  padding: 4px 10px;
  white-space: nowrap;
}
.tt-card h3 {
  font-family: 'Source Serif 4', serif; font-size: 20px; font-weight: 600;
  margin: 6px 0 10px; color: var(--tt-ink);
}
.tt-card .tt-body { color: #2A2F3A; font-size: 14.5px; line-height: 1.55; }
.tt-card mark { background: rgba(255, 213, 79, 0.45); color: inherit; padding: 0 2px; border-radius: 2px; }
.tt-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 12px; }
.tt-tag {
  font-size: 11px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em;
  color: var(--tt-ink-muted); background: rgba(0,0,0,0.04);
  border-radius: 999px; padding: 3px 9px;
}
.tt-card-footer { display: flex; gap: 10px; align-items: center; margin-top: 14px; }
.tt-icon-btn { color: var(--tt-ink-muted); text-decoration: none; font-size: 13px; }
.tt-icon-btn:hover { color: var(--tt-accent); }

/* Pin button — Streamlit button overrides scoped to a wrapper */
.tt-pin-wrap .stButton > button {
  background: transparent !important;
  border: 1px solid var(--tt-hairline) !important;
  color: var(--tt-ink-muted) !important;
  border-radius: 999px !important;
  padding: 4px 10px !important;
  font-size: 12px !important;
  height: auto !important;
  min-height: 0 !important;
}
.tt-pin-wrap .stButton > button:hover {
  border-color: var(--tt-accent) !important;
  color: var(--tt-accent) !important;
}

/* Sidebar (Case File) */
section[data-testid="stSidebar"] {
  background: #0B0D12 !important;
  border-right: 1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] .block-container { padding-top: 24px; }
.tt-sidebar-title {
  font-family: 'Source Serif 4', serif; font-size: 16px; font-weight: 600;
  display: flex; align-items: center; gap: 8px; color: var(--tt-ink-on-dark);
  margin-bottom: 12px;
}
.tt-badge {
  background: var(--tt-accent); color: white; border-radius: 999px;
  padding: 1px 8px; font-size: 11px; font-family: 'JetBrains Mono', monospace; font-weight: 500;
}
.tt-pinned-item {
  padding: 10px 12px; margin-bottom: 6px;
  background: rgba(246,241,231,0.04); border: 1px solid rgba(246,241,231,0.08);
  border-radius: 8px;
}
.tt-pinned-cite {
  font-family: 'JetBrains Mono', monospace; font-size: 11px;
  color: var(--tt-accent); margin-bottom: 2px;
}
.tt-pinned-title { font-size: 12.5px; color: var(--tt-ink-on-dark); line-height: 1.3; }

/* AI memo rail */
.tt-memo {
  background: var(--tt-surface); border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--tt-radius); padding: 22px;
  position: sticky; top: 24px;
}
.tt-memo h2 {
  font-family: 'Source Serif 4', serif; font-size: 18px; font-weight: 600;
  margin: 0 0 14px; color: var(--tt-ink-on-dark);
}
.tt-memo .tt-cite-pill {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace; font-size: 11px;
  color: var(--tt-accent); background: rgba(122,31,43,0.12);
  border: 1px solid rgba(122,31,43,0.3);
  border-radius: 999px; padding: 2px 8px; margin: 0 2px;
  text-decoration: none;
}
.tt-memo .tt-cite-pill:hover { background: rgba(122,31,43,0.24); }

/* Empty / explainer cards */
.tt-explainer { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 20px; }
.tt-explainer .tt-mode-card {
  background: var(--tt-surface); border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--tt-radius); padding: 18px;
}
.tt-mode-card .tt-mode-label {
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--tt-accent); margin-bottom: 6px;
}
.tt-mode-card h4 {
  font-family: 'Source Serif 4', serif; font-size: 16px; font-weight: 600;
  margin: 0 0 6px; color: var(--tt-ink-on-dark);
}
.tt-mode-card p { font-size: 13px; color: var(--tt-ink-muted); margin: 0; line-height: 1.5; }
.tt-mode-card .tt-mode-eg {
  display: inline-block; margin-top: 10px; font-family: 'JetBrains Mono', monospace;
  font-size: 11px; color: var(--tt-ink-on-dark);
  background: rgba(246,241,231,0.06); border-radius: 6px; padding: 4px 8px;
}

/* Skeleton loading */
.tt-skel {
  background: var(--tt-card); border-radius: var(--tt-radius);
  padding: 22px 24px; margin-bottom: 14px; border: 1px solid var(--tt-hairline);
}
.tt-skel-bar {
  height: 14px; border-radius: 6px; margin: 6px 0;
  background: linear-gradient(90deg, rgba(0,0,0,0.06) 25%, rgba(0,0,0,0.12) 37%, rgba(0,0,0,0.06) 63%);
  background-size: 400% 100%;
  animation: tt-shimmer 1.4s infinite ease-in-out;
}
@keyframes tt-shimmer { 0% { background-position: 100% 50%; } 100% { background-position: 0 50%; } }

/* Result count caption */
.tt-route-caption {
  color: var(--tt-ink-muted); font-size: 13px; margin: 6px 0 16px;
  font-family: 'JetBrains Mono', monospace;
}
.tt-route-caption .tt-route-kind { color: var(--tt-accent); font-weight: 500; }

/* Tighten Streamlit horizontal block gaps */
[data-testid="stHorizontalBlock"] { gap: 1.25rem; }

/* Hide the default toggle label spacing weirdness in top bar */
[data-testid="stToggle"] { padding-top: 6px; }
</style>
"""


def inject() -> None:
    """Inject CSS + fonts once per session."""
    if st.session_state.get(_INJECTED_KEY):
        return
    st.markdown(_CSS, unsafe_allow_html=True)
    st.session_state[_INJECTED_KEY] = True
```

- [ ] **Step 2: Verify the module imports**

Run: `python -c "from frontend import styles; print(callable(styles.inject))"`
Expected: `True`

---

## Task 3: Top bar component

**Files:**
- Create: `frontend/components/top_bar.py`

- [ ] **Step 1: Create the top bar**

Write `frontend/components/top_bar.py`:

```python
"""Sticky top bar: wordmark, tagline, AI toggle."""
from __future__ import annotations

import streamlit as st


def render() -> bool:
    """Render the top bar. Returns the AI toggle state."""
    cols = st.columns([6, 1])
    with cols[0]:
        st.markdown(
            """
            <div class="tt-topbar">
              <div style="display:flex; align-items:baseline;">
                <span class="tt-wordmark">TRIAL<span class="tt-dot">·</span>TITANS</span>
                <span class="tt-tagline">Statute search for accident litigation</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cols[1]:
        return st.toggle("AI memo", value=st.session_state.get("use_ai", False), key="use_ai")
```

- [ ] **Step 2: Verify it imports**

Run: `python -c "from frontend.components import top_bar; print(callable(top_bar.render))"`
Expected: `True`

---

## Task 4: Hero search component

**Files:**
- Create: `frontend/components/hero_search.py`

- [ ] **Step 1: Create the hero search**

Write `frontend/components/hero_search.py`:

```python
"""Hero search: large input, jurisdiction picker, example query chips."""
from __future__ import annotations

import streamlit as st

from db.seed import connect

EXAMPLE_QUERIES = [
    "CA Veh Code 22107",
    "rear-ended at a stop sign",
    "failure to yield at intersection",
]


def _jurisdictions() -> list[tuple[str, str]]:
    with connect() as conn:
        return [(r["code"], r["name"]) for r in conn.execute(
            "SELECT code, name FROM jurisdictions ORDER BY name"
        )]


def render() -> tuple[str, str | None]:
    """Render hero search. Returns (query, jurisdiction_code_or_none)."""
    # Apply pending chip-click before rendering the input.
    if "_chip_pending" in st.session_state:
        st.session_state["query"] = st.session_state.pop("_chip_pending")

    cols = st.columns([5, 2])
    with cols[0]:
        query = st.text_input(
            "Search",
            key="query",
            label_visibility="collapsed",
            placeholder="Search by citation, factor, or accident description…",
        )
    with cols[1]:
        juris_options = [("", "Any jurisdiction")] + _jurisdictions()
        jur_label = st.selectbox(
            "Jurisdiction",
            [name for _, name in juris_options],
            label_visibility="collapsed",
        )
        jurisdiction = next((code for code, name in juris_options if name == jur_label), "") or None

    # Example chips
    st.markdown('<div class="tt-chip-row">', unsafe_allow_html=True)
    chip_cols = st.columns(len(EXAMPLE_QUERIES) + 1)
    for i, eg in enumerate(EXAMPLE_QUERIES):
        with chip_cols[i]:
            if st.button(eg, key=f"chip-{i}"):
                st.session_state["_chip_pending"] = eg
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    return query, jurisdiction
```

- [ ] **Step 2: Verify import**

Run: `python -c "from frontend.components import hero_search; print(callable(hero_search.render))"`
Expected: `True`

---

## Task 5: Empty state component

**Files:**
- Create: `frontend/components/empty_state.py`

- [ ] **Step 1: Create the empty state**

Write `frontend/components/empty_state.py`:

```python
"""Landing-state explainer: three retrieval modes with example queries."""
from __future__ import annotations

import streamlit as st

MODES = [
    ("Citation", "Pinpoint a specific section by citation.", "CA Veh Code 22107"),
    ("Factor", "Find statutes by contributing factor.", "failure to yield"),
    ("Description", "Describe the accident in plain English.", "rear-ended at a stop sign"),
]


def render() -> None:
    cards = "".join(
        f"""
        <div class="tt-mode-card">
          <div class="tt-mode-label">{label}</div>
          <h4>{label} search</h4>
          <p>{desc}</p>
          <span class="tt-mode-eg">{eg}</span>
        </div>
        """
        for label, desc, eg in MODES
    )
    st.markdown(
        f"""
        <div class="tt-explainer">
          {cards}
        </div>
        """,
        unsafe_allow_html=True,
    )
```

- [ ] **Step 2: Verify import**

Run: `python -c "from frontend.components import empty_state; print(callable(empty_state.render))"`
Expected: `True`

---

## Task 6: Loading state component

**Files:**
- Create: `frontend/components/loading_state.py`

- [ ] **Step 1: Create the skeleton loader**

Write `frontend/components/loading_state.py`:

```python
"""Skeleton cards shown while results compute."""
from __future__ import annotations

import streamlit as st


def render(count: int = 3) -> None:
    skeletons = "".join(
        """
        <div class="tt-skel">
          <div class="tt-skel-bar" style="width: 30%; height: 12px;"></div>
          <div class="tt-skel-bar" style="width: 70%; height: 18px; margin-top: 12px;"></div>
          <div class="tt-skel-bar" style="width: 100%;"></div>
          <div class="tt-skel-bar" style="width: 90%;"></div>
          <div class="tt-skel-bar" style="width: 40%; margin-top: 10px;"></div>
        </div>
        """
        for _ in range(count)
    )
    st.markdown(skeletons, unsafe_allow_html=True)
```

- [ ] **Step 2: Verify import**

Run: `python -c "from frontend.components import loading_state; print(callable(loading_state.render))"`
Expected: `True`

---

## Task 7: Result card (rewritten)

**Files:**
- Modify (full rewrite): `frontend/components/result_card.py`

The new card has: citation chip + factor tags in the header row, serif title, FTS-highlighted body excerpt, footer with pin button, source link, and "Open" expander for full body.

- [ ] **Step 1: Rewrite the result card**

Write `frontend/components/result_card.py` (overwrite existing):

```python
"""Render a single statute result card."""
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
        # FTS5 snippet may already contain <mark> tags — preserve them.
        return s["snippet"]
    body = s.get("body") or ""
    return _html.escape(body[:400] + ("…" if len(body) > 400 else ""))


def render(statute: dict) -> None:
    sid = statute.get("id", "x")
    cite = _citation(statute)
    title = _html.escape(statute.get("title") or "")
    excerpt = _excerpt(statute)
    factors_html = _factor_tags(statute)
    source_url = statute.get("source_url")

    source_link = (
        f'<a class="tt-icon-btn" href="{_html.escape(source_url)}" target="_blank" rel="noreferrer">↗ Source</a>'
        if source_url else ""
    )

    st.markdown(
        f"""
        <div class="tt-card" id="statute-{sid}">
          <div class="tt-card-header">
            <span class="tt-citation">{_html.escape(cite)}</span>
          </div>
          <h3>{title}</h3>
          <div class="tt-body">{excerpt}</div>
          {factors_html}
          <div class="tt-card-footer">{source_link}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Pin button + Open expander rendered as native Streamlit widgets just below the card.
    pinned_ids = {p["id"] for p in st.session_state.get("case_pinned", [])}
    is_pinned = sid in pinned_ids
    cols = st.columns([1, 1, 6])
    with cols[0]:
        st.markdown('<div class="tt-pin-wrap">', unsafe_allow_html=True)
        label = "📌 Pinned" if is_pinned else "📌 Pin"
        if st.button(label, key=f"pin-{sid}"):
            if is_pinned:
                st.session_state.case_pinned = [
                    p for p in st.session_state.case_pinned if p["id"] != sid
                ]
            else:
                st.session_state.case_pinned.append(statute)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with cols[1]:
        if statute.get("body"):
            with st.expander("Open full text"):
                st.markdown(statute["body"])
```

- [ ] **Step 2: Verify import**

Run: `python -c "from frontend.components import result_card; print(callable(result_card.render))"`
Expected: `True`

---

## Task 8: Case File sidebar

**Files:**
- Create: `frontend/components/case_file_sidebar.py`

- [ ] **Step 1: Create the sidebar**

Write `frontend/components/case_file_sidebar.py`:

```python
"""Left sidebar: pinned statutes, count badge, export button."""
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
            <div class="tt-sidebar-title">
              Case File <span class="tt-badge">{len(pinned)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not pinned:
            st.caption("Pin statutes from the results to build a case file.")
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
                """,
                unsafe_allow_html=True,
            )
            if st.button("Unpin", key=f"unpin-{sid}"):
                st.session_state.case_pinned = [
                    p for p in pinned if p["id"] != sid
                ]
                st.rerun()

        st.divider()
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
```

- [ ] **Step 2: Verify import**

Run: `python -c "from frontend.components import case_file_sidebar; print(callable(case_file_sidebar.render))"`
Expected: `True`

---

## Task 9: AI memo rail

**Files:**
- Create: `frontend/components/ai_memo_rail.py`

The memo rail calls `ai.answer_generator.answer` (a sync call). We post-process the returned text to convert `§ <num>` and `CA Veh Code § <num>` references into anchor pills that scroll-jump to `#statute-<id>` cards. We match section numbers against the current results.

- [ ] **Step 1: Create the memo rail**

Write `frontend/components/ai_memo_rail.py`:

```python
"""Right rail: AI-generated attorney memo with clickable citation pills."""
from __future__ import annotations

import os
import re

import streamlit as st

from ai import answer_generator

_SECTION_RE = re.compile(r"§\s*([0-9.\-]+)")


def _linkify_citations(memo: str, results: list[dict]) -> str:
    """Replace '§ 22107' style refs with anchor pills targeting matching result cards."""
    section_to_id = {}
    for s in results:
        sec = str(s.get("section") or "").strip()
        if sec and sec not in section_to_id:
            section_to_id[sec] = s.get("id")

    def repl(m: re.Match[str]) -> str:
        sec = m.group(1)
        sid = section_to_id.get(sec)
        if sid is None:
            return m.group(0)
        return (
            f'<a class="tt-cite-pill" href="#statute-{sid}">§ {sec}</a>'
        )

    return _SECTION_RE.sub(repl, memo)


def render(query: str, results: list[dict], jurisdiction: str | None) -> None:
    if not results:
        return

    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.markdown(
            """
            <div class="tt-memo">
              <h2>AI Memo</h2>
              <p style="color: var(--tt-ink-muted); font-size: 13px;">
                Set <code>ANTHROPIC_API_KEY</code> to enable the AI memo.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    cache_key = ("memo", query, jurisdiction, tuple(s.get("id") for s in results))
    if st.session_state.get("_memo_cache_key") != cache_key:
        with st.spinner("Drafting attorney memo…"):
            memo_text = answer_generator.answer(query, results, jurisdiction=jurisdiction)
        st.session_state["last_memo"] = memo_text
        st.session_state["_memo_cache_key"] = cache_key
    else:
        memo_text = st.session_state.get("last_memo", "")

    body_html = _linkify_citations(memo_text, results).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="tt-memo">
          <h2>AI Memo</h2>
          <div style="font-size: 14px; line-height: 1.6; color: var(--tt-ink-on-dark);">
            {body_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
```

- [ ] **Step 2: Verify import**

Run: `python -c "from frontend.components import ai_memo_rail; print(callable(ai_memo_rail.render))"`
Expected: `True`

---

## Task 10: Rewrite `streamlit_app.py`

**Files:**
- Modify (full rewrite): `frontend/streamlit_app.py`

This is the orchestrator. It injects styles, renders the top bar + sidebar, sets up the two-column main layout (results / AI rail), and dispatches between empty / loading / results states.

- [ ] **Step 1: Rewrite the entrypoint**

Write `frontend/streamlit_app.py` (overwrite existing):

```python
"""TrialTitans — Streamlit UI for the Legal Statute Harvester."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from frontend import styles
from frontend.components import (
    ai_memo_rail,
    case_file_sidebar,
    empty_state,
    hero_search,
    result_card,
    top_bar,
)
from retrieval import query_router, reranker

st.set_page_config(
    page_title="TrialTitans — Statute Search",
    layout="wide",
    initial_sidebar_state="expanded",
)

styles.inject()

if "case_pinned" not in st.session_state:
    st.session_state.case_pinned = []

case_file_sidebar.render()

use_ai = top_bar.render()

query, jurisdiction = hero_search.render()

if not query:
    empty_state.render()
    st.stop()

routed = query_router.route(query, jurisdiction=jurisdiction or None, limit=20)
results = routed["results"]

if use_ai and routed["kind"] == "fts" and results:
    results = reranker.rerank(query, results, top_k=8)

st.session_state["last_results"] = results

st.markdown(
    f'<div class="tt-route-caption">route <span class="tt-route-kind">{routed["kind"]}</span> · {len(results)} result(s)</div>',
    unsafe_allow_html=True,
)

if not results:
    st.markdown(
        '<div class="tt-card"><h3>No statutes matched</h3>'
        '<div class="tt-body">Try a different phrasing or one of the example chips above.</div></div>',
        unsafe_allow_html=True,
    )
    st.stop()

main_col, rail_col = st.columns([3, 2]) if use_ai else (st.container(), None)

with main_col:
    for s in results:
        result_card.render(s)

if use_ai and rail_col is not None:
    with rail_col:
        ai_memo_rail.render(query, results, jurisdiction)
```

- [ ] **Step 2: Verify the module imports**

Run: `python -c "import sys; sys.path.insert(0, '.'); import frontend.streamlit_app" 2>&1 | tail -5`
Expected: no traceback (Streamlit may emit a warning about running outside `streamlit run`; that's fine — only an actual ImportError or AttributeError matters).

---

## Task 11: Delete dead components

**Files:**
- Delete: `frontend/components/search_bar.py`
- Delete: `frontend/components/case_workspace.py`

These were replaced by `hero_search.py` and `case_file_sidebar.py`. No callers remain (verified by grep in step 1).

- [ ] **Step 1: Confirm no remaining references**

Run: `grep -rn "components.search_bar\|components.case_workspace\|from frontend.components import.*search_bar\|from frontend.components import.*case_workspace" frontend/ tests/ 2>/dev/null`
Expected: no output (or only matches inside the files about to be deleted).

If any external references appear, stop and update them before deleting.

- [ ] **Step 2: Delete the files**

Run:
```bash
rm frontend/components/search_bar.py frontend/components/case_workspace.py
```

- [ ] **Step 3: Verify deletion**

Run: `ls frontend/components/`
Expected output should NOT include `search_bar.py` or `case_workspace.py`. Should include the new component files.

---

## Task 12: Smoke test

**Files:**
- Create: `tests/test_frontend_smoke.py`

A single test that imports every new frontend module and confirms each public render function is callable. This catches the most common breakages (typos, missing imports, syntax errors) without trying to assert visual behavior.

- [ ] **Step 1: Write the smoke test**

Write `tests/test_frontend_smoke.py`:

```python
"""Smoke tests: every frontend module imports and exposes its render entrypoint."""
from __future__ import annotations

import importlib

import pytest


@pytest.mark.parametrize(
    "module_name, attr",
    [
        ("frontend.styles", "inject"),
        ("frontend.components.top_bar", "render"),
        ("frontend.components.hero_search", "render"),
        ("frontend.components.empty_state", "render"),
        ("frontend.components.loading_state", "render"),
        ("frontend.components.result_card", "render"),
        ("frontend.components.case_file_sidebar", "render"),
        ("frontend.components.ai_memo_rail", "render"),
    ],
)
def test_module_exposes_callable(module_name: str, attr: str) -> None:
    mod = importlib.import_module(module_name)
    assert callable(getattr(mod, attr)), f"{module_name}.{attr} should be callable"


def test_streamlit_app_imports() -> None:
    """The entrypoint script should import without raising."""
    importlib.import_module("frontend.streamlit_app")


def test_old_components_removed() -> None:
    """The replaced components should no longer be importable."""
    for old in ("frontend.components.search_bar", "frontend.components.case_workspace"):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(old)
```

- [ ] **Step 2: Run the smoke test**

Run: `pytest tests/test_frontend_smoke.py -v`
Expected: all tests PASS. If any test fails, fix the underlying module — do not edit the test to make it pass.

- [ ] **Step 3: Run the full test suite**

Run: `pytest -q`
Expected: no regressions versus pre-redesign. Existing retrieval/citation/factor tests should still pass.

---

## Task 13: Manual demo verification

**Files:** none — manual run.

This is the acceptance gate. Each item maps to an acceptance criterion in the spec.

- [ ] **Step 1: Launch the app**

Run: `streamlit run frontend/streamlit_app.py`
Expected: opens at `http://localhost:8501` without runtime errors in the terminal.

- [ ] **Step 2: Verify the landing state**

In the browser:
- Wordmark "TRIAL·TITANS" with serif font visible top-left.
- Tagline "Statute search for accident litigation" next to it.
- AI toggle visible top-right.
- Hero search input with placeholder text.
- Three example chips below the search input.
- Three explainer cards (Citation / Factor / Description) below.
- Left sidebar shows "Case File" with a `0` badge and the empty-state caption.

- [ ] **Step 3: Verify chip click → results**

Click the chip "rear-ended at a stop sign".
Expected: query populates, route caption appears (`route fts · N result(s)`), result cards render with citation chip, serif title, body excerpt (with highlight if FTS), factor tags (if any).

- [ ] **Step 4: Verify pinning**

Click "📌 Pin" on two cards.
Expected: button label changes to "📌 Pinned", sidebar count badge updates, two `tt-pinned-item` rows appear in the sidebar.

- [ ] **Step 5: Verify AI memo rail (if `ANTHROPIC_API_KEY` is set)**

Toggle AI on (top-right).
Expected: a right rail appears with the AI memo. References like `§ 22107` should render as clickable pill links. Clicking one scrolls the matching result card into view.

If `ANTHROPIC_API_KEY` is NOT set: the rail shows the "Set ANTHROPIC_API_KEY to enable" note instead of crashing.

- [ ] **Step 6: Verify export**

In the sidebar, click "Export memo".
Expected: a `case_file.md` download containing the pinned statutes (and the AI memo if one was generated).

- [ ] **Step 7: Verify "no results" state**

Type a deliberately bogus query (e.g., `zzzqqq nonsense`).
Expected: a card-styled "No statutes matched" message rather than a blank page or default Streamlit chrome.

- [ ] **Step 8: Visual polish check**

Confirm: dark background, ivory cards, oxblood accent, serif headings, mono citation chips. No leftover default Streamlit chrome (hamburger menu, header bar, "Made with Streamlit" footer).

---

## Task 14: Final commit

**Files:** all redesign files.

Per user feedback: ALL committing is deferred to this final task. No commits happen between tasks.

- [ ] **Step 1: Review staged changes**

Run: `git status` and `git diff --stat`
Expected: shows the new `.streamlit/`, `frontend/styles.py`, `frontend/components/*.py` (new + rewritten), rewritten `frontend/streamlit_app.py`, deletions of `search_bar.py` and `case_workspace.py`, plus `tests/test_frontend_smoke.py` and the spec/plan docs.

- [ ] **Step 2: Stage the redesign**

Run:
```bash
git add .streamlit/config.toml \
        frontend/streamlit_app.py \
        frontend/styles.py \
        frontend/components/top_bar.py \
        frontend/components/hero_search.py \
        frontend/components/result_card.py \
        frontend/components/case_file_sidebar.py \
        frontend/components/ai_memo_rail.py \
        frontend/components/empty_state.py \
        frontend/components/loading_state.py \
        tests/test_frontend_smoke.py \
        docs/superpowers/specs/2026-05-09-frontend-redesign-design.md \
        docs/superpowers/plans/2026-05-09-frontend-redesign.md
git add -u frontend/components/search_bar.py frontend/components/case_workspace.py
```

- [ ] **Step 3: Commit**

Run:
```bash
git commit -m "$(cat <<'EOF'
feat(frontend): hackathon redesign — top bar, hero search, case file sidebar, AI memo rail

Replaces the default Streamlit demo aesthetic with a custom dark/ivory legal-research
look: serif headings, oxblood accent, citation chips, factor tags, sticky AI memo
with clickable citation pills, persistent left sidebar case file with markdown export.

Stack unchanged (Streamlit + SQLite + Claude). Theming via .streamlit/config.toml
plus a single CSS injection in frontend/styles.py.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 4: Verify commit**

Run: `git log --oneline -2`
Expected: the new commit on top of `69922ad initial commit`.

---

## Self-Review Checklist (already run inline; documenting here for transparency)

**Spec coverage:**
- Visual language (palette/type/spacing) → Task 2 (`styles.py`).
- Layout (top bar / sidebar / main / right rail) → Tasks 3, 8, 10 + CSS in Task 2.
- Components (top_bar, hero_search, result_card, case_file_sidebar, ai_memo_rail, empty_state, loading_state) → Tasks 3–9.
- Theming approach (config.toml + style injector) → Tasks 1, 2.
- File structure → matches the "After this plan" tree above.
- State (`query`, `case_pinned`, `last_memo`, `last_results`, `use_ai`) → set in Tasks 4, 7, 9, 10.
- Error/edge cases (no results, no API key, empty case file) → Tasks 9 (no key), 10 (no results), 8 (export with empty list — disabled-style via early return).
- Acceptance criteria → Task 13 step-by-step.

**Placeholder scan:** no TODOs, TBDs, or "implement later". All code blocks contain runnable code.

**Type/name consistency:**
- `case_pinned` used consistently across `result_card`, `case_file_sidebar`, `streamlit_app`.
- `last_memo` written in `ai_memo_rail`, read in `case_file_sidebar`.
- `query` session-state key written by `hero_search` (chip handler), used by router in `streamlit_app`.
- Anchor IDs `statute-<id>` written in `result_card` HTML, targeted by `ai_memo_rail._linkify_citations`.

**Open implementation choices acknowledged in spec** (not blockers):
- Memo streaming → not implemented; spec called this out as optional. Spinner + final block is what we ship.
- Citation regex format → covered by `_SECTION_RE = r"§\s*([0-9.\-]+)"`.
