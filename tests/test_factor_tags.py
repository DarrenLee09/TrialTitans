"""Tests for retrieval._tags.attach_factor_tags."""
from __future__ import annotations

from db.seed import connect
from retrieval._tags import attach_factor_tags


def _seed_statute_with_tags(jurisdiction_code: str, section: str, factors: list[tuple[str, float]]) -> int:
    """Insert one statute and tag it with the given (factor_code, confidence) pairs."""
    with connect() as conn:
        jur_id = conn.execute(
            "SELECT id FROM jurisdictions WHERE code = ?", (jurisdiction_code,)
        ).fetchone()["id"]
        cur = conn.execute(
            """
            INSERT INTO statutes(jurisdiction_id, citation, section_number, title, full_text, source_url)
            VALUES (?, ?, ?, '', 'body', 'https://example.com')
            """,
            (jur_id, f"{jurisdiction_code} Veh Code §{section}", section),
        )
        statute_id = cur.lastrowid
        for code, conf in factors:
            factor_row = conn.execute(
                "SELECT id FROM contributing_factors WHERE code = ?", (code,)
            ).fetchone()
            assert factor_row, f"factor {code} not seeded — did seed.main() run?"
            conn.execute(
                """
                INSERT INTO statute_factor_tags(statute_id, factor_id, confidence, tagged_by)
                VALUES (?, ?, ?, 'manual')
                """,
                (statute_id, factor_row["id"], conf),
            )
        conn.commit()
        return statute_id


def test_attach_factor_tags_adds_factors_field():
    sid = _seed_statute_with_tags("CA", "99001", [("DUI_DWI", 0.9)])
    rows = [{"id": sid, "section": "99001"}]

    with connect() as conn:
        result = attach_factor_tags(conn, rows)

    assert result is rows  # mutates in place
    assert "factors" in rows[0]
    assert len(rows[0]["factors"]) == 1
    assert rows[0]["factors"][0]["code"] == "DUI_DWI"
    assert rows[0]["factors"][0]["confidence"] == 0.9
    assert rows[0]["factors"][0]["tagged_by"] == "manual"
    assert "label" in rows[0]["factors"][0]


def test_attach_factor_tags_handles_multiple_factors_per_statute():
    sid = _seed_statute_with_tags(
        "CA",
        "99002",
        [("DUI_DWI", 1.0), ("RECKLESS_DRIVING", 0.7)],
    )
    rows = [{"id": sid}]

    with connect() as conn:
        attach_factor_tags(conn, rows)

    codes = {f["code"] for f in rows[0]["factors"]}
    assert codes == {"DUI_DWI", "RECKLESS_DRIVING"}


def test_attach_factor_tags_handles_untagged_statute():
    sid = _seed_statute_with_tags("CA", "99003", [])
    rows = [{"id": sid}]

    with connect() as conn:
        attach_factor_tags(conn, rows)

    assert rows[0]["factors"] == []


def test_attach_factor_tags_handles_empty_input():
    with connect() as conn:
        result = attach_factor_tags(conn, [])
    assert result == []


def test_attach_factor_tags_batches_one_query_for_many_rows():
    sid_a = _seed_statute_with_tags("CA", "99004", [("DUI_DWI", 1.0)])
    sid_b = _seed_statute_with_tags("CA", "99005", [("RECKLESS_DRIVING", 0.5)])
    rows = [{"id": sid_a}, {"id": sid_b}]

    with connect() as conn:
        attach_factor_tags(conn, rows)

    by_id = {r["id"]: r for r in rows}
    assert by_id[sid_a]["factors"][0]["code"] == "DUI_DWI"
    assert by_id[sid_b]["factors"][0]["code"] == "RECKLESS_DRIVING"
