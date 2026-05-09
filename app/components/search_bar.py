"""Three-tab search UI: Citation / Contributing Factor / Natural Language."""
from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from db.seed import connect
from retrieval import citation_parser, exact_lookup, factor_search, fts_search


@dataclass
class SearchOutcome:
    kind: str                      # "citation" | "factor" | "nl"
    query: str                     # raw user input (for downstream prompts)
    results: list[dict]
    jurisdiction: str | None = None


def _jurisdictions() -> list[tuple[str, str]]:
    with connect() as conn:
        return [(r["code"], r["name"])
                for r in conn.execute("SELECT code, name FROM jurisdictions ORDER BY name")]


def _jurisdiction_picker(label: str = "Jurisdiction", key: str = "jur") -> str | None:
    options = [("", "Any jurisdiction")] + _jurisdictions()
    chosen_label = st.selectbox(label, [name for _, name in options], key=key)
    return next((code for code, name in options if name == chosen_label), "") or None


def render() -> SearchOutcome | None:
    citation_tab, factor_tab, nl_tab = st.tabs(
        ["📜 Citation", "🏷️ Contributing factor", "💬 Natural language"]
    )

    # ── Tab 1: Citation lookup ──────────────────────────────────────────────
    with citation_tab:
        cite_in = st.text_input(
            "Citation",
            placeholder="e.g. Cal. Veh. Code § 23152(a)  ·  CA §22107  ·  CA Veh Code 22350",
            key="cite_input",
        )
        if cite_in:
            parsed = citation_parser.parse(cite_in)
            if not parsed:
                st.warning("Couldn't parse that as a citation. Try `CA §22107` or `Cal. Veh. Code § 23152(a)`.")
                return SearchOutcome(kind="citation", query=cite_in, results=[])
            hit = exact_lookup.lookup(parsed)
            return SearchOutcome(
                kind="citation",
                query=cite_in,
                results=[hit] if hit else [],
                jurisdiction=parsed.jurisdiction,
            )

    # ── Tab 2: Contributing factor ──────────────────────────────────────────
    with factor_tab:
        factors = factor_search.list_factors()
        if not factors:
            st.info("No contributing factors loaded yet. Run `python -m db.seed` after dropping the eval CSV into `data/`.")
            return None

        col1, col2 = st.columns([3, 1])
        labels = ["— pick a factor —"] + [f["label"] for f in factors]
        chosen = col1.selectbox("Contributing factor", labels, key="factor_pick")
        with col2:
            jur = _jurisdiction_picker(key="factor_jur")

        if chosen and chosen != labels[0]:
            code = next(f["code"] for f in factors if f["label"] == chosen)
            results = factor_search.by_factor(code, jurisdiction=jur, limit=50)
            return SearchOutcome(kind="factor", query=chosen, results=results, jurisdiction=jur)

    # ── Tab 3: Natural language ─────────────────────────────────────────────
    with nl_tab:
        col1, col2 = st.columns([3, 1])
        nl_in = col1.text_input(
            "Describe the situation or question",
            placeholder="e.g. rear-ended at a stop sign  ·  distracted driving laws in California",
            key="nl_input",
        )
        with col2:
            jur = _jurisdiction_picker(key="nl_jur")

        if nl_in:
            results = fts_search.search(nl_in, jurisdiction=jur, limit=20)
            return SearchOutcome(kind="nl", query=nl_in, results=results, jurisdiction=jur)

    return None
