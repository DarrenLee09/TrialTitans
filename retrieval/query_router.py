"""Decide which retrieval path a user query should take."""
from __future__ import annotations

from typing import Literal, TypedDict

from retrieval import citation_parser, exact_lookup, factor_search, fts_search

QueryKind = Literal["citation", "factor", "fts"]


class RoutedResult(TypedDict):
    kind: QueryKind
    results: list[dict]


def _factor_slug_for(query: str) -> str | None:
    q = query.lower()
    for f in factor_search.list_factors():
        if f["slug"] in q or f["label"].lower() in q:
            return f["slug"]
    return None


def route(query: str, jurisdiction: str | None = None, limit: int = 20) -> RoutedResult:
    citation = citation_parser.parse(query)
    if citation:
        hit = exact_lookup.lookup(citation)
        return {"kind": "citation", "results": [hit] if hit else []}

    factor = _factor_slug_for(query)
    if factor:
        return {
            "kind": "factor",
            "results": factor_search.by_factor(factor, jurisdiction=jurisdiction, limit=limit),
        }

    return {
        "kind": "fts",
        "results": fts_search.search(query, jurisdiction=jurisdiction, limit=limit),
    }
