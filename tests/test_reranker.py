"""Tests for retrieval.reranker.

The Claude path is exercised opportunistically when ANTHROPIC_API_KEY is set;
the offline behaviour and the rank/explanation merge helper are the always-on
contracts and are covered here.
"""
from __future__ import annotations

from retrieval.reranker import _apply_order, rerank


def test_apply_order_attaches_explanations_in_returned_order():
    candidates = [{"id": 1, "title": "a"}, {"id": 2, "title": "b"}]
    ranking = [
        {"id": 2, "why": "directly answers the question"},
        {"id": 1, "why": "background context"},
    ]
    out = _apply_order(candidates, ranking, top_k=2)
    assert [c["id"] for c in out] == [2, 1]
    assert out[0]["explanation"] == "directly answers the question"
    assert out[1]["explanation"] == "background context"


def test_apply_order_skips_unknown_ids():
    candidates = [{"id": 1}]
    ranking = [{"id": 99, "why": "ghost"}, {"id": 1, "why": "real"}]
    out = _apply_order(candidates, ranking, top_k=5)
    assert len(out) == 1
    assert out[0]["id"] == 1
    assert out[0]["explanation"] == "real"


def test_apply_order_truncates_to_top_k():
    candidates = [{"id": i} for i in range(5)]
    ranking = [{"id": i, "why": str(i)} for i in range(5)]
    out = _apply_order(candidates, ranking, top_k=3)
    assert len(out) == 3


def test_apply_order_falls_back_when_ranking_is_empty():
    candidates = [{"id": 1}, {"id": 2}]
    out = _apply_order(candidates, [], top_k=2)
    # When Claude gives nothing usable, return the original top_k.
    assert [c["id"] for c in out] == [1, 2]
    # No explanation when we couldn't get one.
    assert "explanation" not in out[0]


def test_apply_order_does_not_mutate_input_dicts():
    original = {"id": 1, "title": "a"}
    candidates = [original]
    ranking = [{"id": 1, "why": "because"}]
    _apply_order(candidates, ranking, top_k=1)
    assert "explanation" not in original


def test_apply_order_handles_missing_why():
    candidates = [{"id": 1}]
    ranking = [{"id": 1}]  # no "why" key
    out = _apply_order(candidates, ranking, top_k=1)
    assert out[0]["id"] == 1
    assert out[0]["explanation"] == ""


def test_rerank_offline_returns_first_top_k_unchanged():
    """Without an API key (or anthropic SDK), rerank is a no-op slice."""
    candidates = [{"id": 1}, {"id": 2}, {"id": 3}]
    out = rerank("query", candidates, top_k=2)
    assert [c["id"] for c in out] == [1, 2]


def test_rerank_empty_candidates_returns_empty():
    assert rerank("query", [], top_k=5) == []
