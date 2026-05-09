from db.seed import connect
from harvester.build_fts_index import rebuild
from retrieval import fts_search


def test_fts_finds_statute_by_keyword():
    with connect() as conn:
        conn.execute(
            "INSERT INTO statutes(jurisdiction, code_name, section, title, body) "
            "VALUES ('CA', 'Vehicle Code', '22107', 'Turning movements', "
            "'No person shall turn a vehicle without giving an appropriate signal.')"
        )
        conn.commit()

    rebuild()
    hits = fts_search.search("turn signal", jurisdiction="CA")
    assert any(h["section"] == "22107" for h in hits)
