"""Decide which retrieval path a user query should take."""
from __future__ import annotations

from typing import Literal, TypedDict

from retrieval import citation_parser, exact_lookup, factor_search, fts_search

QueryKind = Literal["citation", "factor", "fts"]


class RoutedResult(TypedDict):
    kind: QueryKind
    results: list[dict]


def _factor_code_for(query: str) -> str | None:
    """Match query text against known factor codes/labels (bidirectional substring)."""
    q = query.lower().strip()
    if len(q) < 3:
        return None
    for f in factor_search.list_factors():
        code = f["code"].lower()
        label = f["label"].lower()
        if q in (code, label) or q in code or q in label or code in q or label in q:
            return f["code"]
    return None


def route(query: str, jurisdiction: str | None = None, limit: int = 20) -> RoutedResult:
    citation = citation_parser.parse(query)
    if citation:
        hit = exact_lookup.lookup(citation)
        return {"kind": "citation", "results": [hit] if hit else []}

    factor_code = _factor_code_for(query)
    if factor_code:
        return {
            "kind": "factor",
            "results": factor_search.by_factor(factor_code, jurisdiction=jurisdiction, limit=limit),
        }

    return {
        "kind": "fts",
        "results": fts_search.search(query, jurisdiction=jurisdiction, limit=limit),
    }
