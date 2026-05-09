"""Hybrid query router.

Three lanes:
    1. Citation parse hits          → exact_lookup (kind="citation")
    2. Everything else (NL queries) → interpreter extracts {jurisdictions, factors,
       intent}; the router then runs factor_search (per matched factor) +
       FTS (on `intent`) + vector_search (on the original query) in parallel and
       merges the ranked lists with reciprocal-rank fusion (kind="hybrid").

Vector search is a first-class participant in the merge, not a fallback for
empty FTS results. RRF naturally weights statutes that appear in multiple
lanes higher than singletons.
"""
from __future__ import annotations

import sqlite3
from typing import Iterable, Literal, TypedDict

from ai.query_interpreter import interpret
from retrieval import citation_parser, exact_lookup, factor_search, fts_search, vector_search

QueryKind = Literal["citation", "hybrid"]
RRF_K = 60


class RoutedResult(TypedDict):
    kind: QueryKind
    results: list[dict]


def rrf_merge(lists: Iterable[list[dict]], k: int = RRF_K) -> list[dict]:
    """Reciprocal-rank fusion. score(id) = Σ over lists of 1 / (k + rank).

    Dedupes by `id`. The first dict seen for a given id wins for the result
    shape (so we keep the snippet/score from whichever lane saw it first).
    """
    scores: dict = {}
    first_seen: dict = {}
    for ranked in lists:
        for rank, row in enumerate(ranked):
            sid = row.get("id")
            if sid is None:
                continue
            scores[sid] = scores.get(sid, 0.0) + 1.0 / (k + rank + 1)
            first_seen.setdefault(sid, row)
    return [first_seen[sid] for sid in sorted(scores, key=lambda s: -scores[s])]


def route(query: str, jurisdiction: str | None = None, limit: int = 20) -> RoutedResult:
    citation = citation_parser.parse(query)
    if citation:
        hit = exact_lookup.lookup(citation)
        return {"kind": "citation", "results": [hit] if hit else []}

    parsed = interpret(query)
    # Explicit user filter wins; otherwise use the first jurisdiction the interpreter
    # extracted. (Multi-jurisdiction comparison is a future feature — today the
    # search functions only accept a single code.)
    jur_filter = jurisdiction or (parsed["jurisdictions"][0] if parsed["jurisdictions"] else None)
    intent = parsed["intent"].strip() or query

    lists: list[list[dict]] = []

    for code in parsed["factors"]:
        lists.append(factor_search.by_factor(code, jurisdiction=jur_filter, limit=limit))

    try:
        lists.append(fts_search.search(intent, jurisdiction=jur_filter, limit=limit))
    except sqlite3.OperationalError:
        # FTS5 rejects some inputs (e.g. lone punctuation); treat as no contribution.
        pass

    if vector_search.has_embeddings(jurisdiction=jur_filter):
        lists.append(vector_search.search(query, jurisdiction=jur_filter, limit=limit))

    merged = rrf_merge(lists)[:limit]
    return {"kind": "hybrid", "results": merged}
