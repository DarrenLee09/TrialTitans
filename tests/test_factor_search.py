from db.seed import connect
from retrieval import factor_search


def _insert_statute(jurisdiction_code: str, section: str, body: str) -> int:
    with connect() as conn:
        jur_id = conn.execute(
            "SELECT id FROM jurisdictions WHERE code = ?", (jurisdiction_code,)
        ).fetchone()["id"]
        cur = conn.execute(
            """
            INSERT INTO statutes(jurisdiction_id, citation, section_number, title, full_text, source_url)
            VALUES (?, ?, ?, '', ?, 'https://example.com')
            """,
            (jur_id, f"{jurisdiction_code} Veh Code §{section}", section, body),
        )
        conn.commit()
        return cur.lastrowid


def test_factors_seeded():
    factors = factor_search.list_factors()
    codes = {f["code"] for f in factors}
    assert "DUI_DWI" in codes
    assert "FAILURE_TO_YIELD_AT_A_YIELD_SIGN" in codes


def test_factor_search_finds_tagged_statute():
    from harvester.classify_factors import classify_all

    _insert_statute("CA", "23103", "No person shall operate a vehicle with a reckless driving disregard for safety.")
    classify_all()
    hits = factor_search.by_factor("RECKLESS_DRIVING", jurisdiction="CA")
    assert any(h["section"] == "23103" for h in hits)
