from db.seed import connect
from retrieval import factor_search


def _insert_statute(jurisdiction: str, section: str, body: str) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO statutes(jurisdiction, code_name, section, title, body) VALUES (?, 'Vehicle Code', ?, '', ?)",
            (jurisdiction, section, body),
        )
        conn.commit()
        return cur.lastrowid


def test_factors_seeded():
    factors = factor_search.list_factors()
    slugs = {f["slug"] for f in factors}
    assert "dui" in slugs
    assert "failure_to_yield" in slugs


def test_factor_search_finds_tagged_statute():
    from harvester.classify_factors import classify_all

    _insert_statute("CA", "23152", "It is unlawful to drive under the influence of alcohol.")
    classify_all()
    hits = factor_search.by_factor("dui", jurisdiction="CA")
    assert any(h["section"] == "23152" for h in hits)
