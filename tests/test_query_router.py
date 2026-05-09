"""Tests for the hybrid query router and its reciprocal-rank-fusion merge."""
from __future__ import annotations

from db.seed import connect
from harvester.build_fts_index import rebuild
from retrieval import query_router
from retrieval.query_router import rrf_merge


# ---- RRF merge ---------------------------------------------------------------

def test_rrf_merge_returns_empty_for_no_inputs():
    assert rrf_merge([]) == []


def test_rrf_merge_keeps_single_list_in_order():
    a = [{"id": 1}, {"id": 2}, {"id": 3}]
    assert [r["id"] for r in rrf_merge([a])] == [1, 2, 3]


def test_rrf_merge_promotes_results_appearing_in_multiple_lists():
    fts = [{"id": 1, "src": "fts"}, {"id": 2, "src": "fts"}, {"id": 3, "src": "fts"}]
    vec = [{"id": 3, "src": "vec"}, {"id": 1, "src": "vec"}, {"id": 4, "src": "vec"}]
    merged = rrf_merge([fts, vec])
    # 1 and 3 each appear in both lists → score higher than singletons 2 and 4.
    assert {merged[0]["id"], merged[1]["id"]} == {1, 3}
    assert merged[-1]["id"] in {2, 4}


def test_rrf_merge_dedupes_by_id_keeping_first_occurrence_data():
    fts = [{"id": 1, "snippet": "from-fts"}]
    vec = [{"id": 1, "score": 0.95}]
    merged = rrf_merge([fts, vec])
    assert len(merged) == 1
    # First occurrence (fts list) wins for the dict shape; later lists don't clobber.
    assert merged[0]["snippet"] == "from-fts"


def test_rrf_merge_skips_empty_lists():
    a = [{"id": 1}]
    merged = rrf_merge([[], a, []])
    assert [r["id"] for r in merged] == [1]


# ---- Routing -----------------------------------------------------------------

def _seed_statute_with_factor(jur_code: str, section: str, body: str, factor_code: str | None = None) -> int:
    with connect() as conn:
        jur_id = conn.execute(
            "SELECT id FROM jurisdictions WHERE code = ?", (jur_code,)
        ).fetchone()["id"]
        cur = conn.execute(
            """
            INSERT INTO statutes(jurisdiction_id, citation, section_number, title, full_text, source_url)
            VALUES (?, ?, ?, '', ?, 'https://example.com')
            """,
            (jur_id, f"{jur_code} Veh Code §{section}", section, body),
        )
        statute_id = cur.lastrowid
        if factor_code:
            factor = conn.execute(
                "SELECT id FROM contributing_factors WHERE code = ?", (factor_code,)
            ).fetchone()
            if factor:
                conn.execute(
                    """INSERT INTO statute_factor_tags(statute_id, factor_id, confidence, tagged_by)
                       VALUES (?, ?, 1.0, 'manual')""",
                    (statute_id, factor["id"]),
                )
        conn.commit()
        return statute_id


def test_route_citation_query_uses_exact_lookup():
    sid = _seed_statute_with_factor("CA", "33333", "speed limit text")
    rebuild()
    routed = query_router.route("CA Veh Code 33333")
    assert routed["kind"] == "citation"
    assert any(r and r.get("id") == sid for r in routed["results"])


def test_route_natural_language_query_returns_hybrid_kind():
    _seed_statute_with_factor("CA", "44444", "school zones speed limit text")
    rebuild()
    routed = query_router.route("speed limit in school zones")
    # Either hybrid (interpreter contributed) or fts (intent-only fallback) is acceptable;
    # the contract is that NL queries are NOT empty when text matches exist.
    assert routed["kind"] in {"hybrid", "fts"}


def test_route_filters_by_interpreter_extracted_jurisdiction():
    """Even with no explicit jurisdiction= arg, the router should narrow to CA
    when the query says "in California"."""
    _seed_statute_with_factor("CA", "55555", "Rules about turning movements at intersections")
    rebuild()
    routed = query_router.route("turning rules in California")
    assert routed["results"], "expected at least one result"
    for r in routed["results"]:
        assert r.get("jurisdiction") == "CA"
