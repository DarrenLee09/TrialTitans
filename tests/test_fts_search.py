from db.seed import connect
from harvester.build_fts_index import rebuild
from retrieval import fts_search


def _insert_statute(section: str, title: str, body: str) -> None:
    with connect() as conn:
        jur_id = conn.execute(
            "SELECT id FROM jurisdictions WHERE code = 'CA'"
        ).fetchone()["id"]
        conn.execute(
            """
            INSERT OR IGNORE INTO statutes(jurisdiction_id, citation, section_number, title, full_text, source_url)
            VALUES (?, ?, ?, ?, ?, 'https://example.com')
            """,
            (jur_id, f"CA Veh Code §{section}", section, title, body),
        )
        conn.commit()


def test_fts_finds_statute_by_keyword():
    _insert_statute(
        "22107",
        "Turning movements",
        "No person shall turn a vehicle without giving an appropriate signal.",
    )
    rebuild()
    hits = fts_search.search("turn signal", jurisdiction="CA")
    assert any(h["section"] == "22107" for h in hits)
