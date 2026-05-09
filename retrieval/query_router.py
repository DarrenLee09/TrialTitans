"""Decide which retrieval path a user query should take."""
from __future__ import annotations

from typing import Literal, TypedDict

from retrieval import citation_parser, exact_lookup, factor_search, fts_search, live_fetch, vector_search

QueryKind = Literal["citation", "live", "factor", "fts", "semantic"]


class RoutedResult(TypedDict):
    kind: QueryKind
    results: list[dict]


def _factor_slug_for(query: str) -> str | None:
    """Match a free-text query to a factor by overlapping word tokens.

    Substring matching ("dui" in "dui_dwi") only worked one direction and
    missed short queries. Token overlap handles both: query "DUI" → factor
    "DUI/DWI" matches via the shared "dui" token.
    """
    import re
    STOP = {"a", "an", "the", "of", "and", "or", "to", "for", "in", "on",
            "with", "from", "at", "by"}
    q_tokens = {t for t in re.findall(r"[a-z0-9]+", query.lower())} - STOP
    if not q_tokens:
        return None
    # Short query (e.g. "DUI") matches on a single shared token; longer
    # natural-language phrases require ≥2 overlapping tokens so we don't
    # latch onto incidental words ("stop sign" matching "Failure to Yield
    # at a Yield Sign" via just "sign").
    required = 1 if len(q_tokens) <= 2 else 2
    for f in factor_search.list_factors():
        label_tokens = {t for t in re.findall(r"[a-z0-9]+", f["label"].lower())} - STOP
        if len(q_tokens & label_tokens) >= required:
            return f["code"]
    return None


def route(query: str, jurisdiction: str | None = None, limit: int = 20) -> RoutedResult:
    citation = citation_parser.parse(query)
    if citation:
        hit = exact_lookup.lookup(citation)
        if hit:
            return {"kind": "citation", "results": [hit]}
        live = live_fetch.fetch(citation.jurisdiction, citation.code_name, citation.section)
        if live:
            return {"kind": "live", "results": [live]}
        return {"kind": "citation", "results": []}

    factor = _factor_slug_for(query)
    if factor:
        return {
            "kind": "factor",
            "results": factor_search.by_factor(factor, jurisdiction=jurisdiction, limit=limit),
        }

    fts_results = fts_search.search(query, jurisdiction=jurisdiction, limit=limit)
    if fts_results:
        return {"kind": "fts", "results": fts_results}

    if vector_search.has_embeddings(jurisdiction=jurisdiction):
        return {
            "kind": "semantic",
            "results": vector_search.search(query, jurisdiction=jurisdiction, limit=limit),
        }

    return {"kind": "fts", "results": []}
