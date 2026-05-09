"""Exact SQL lookup by (jurisdiction code, section number)."""
from __future__ import annotations

from db.seed import connect
from retrieval.citation_parser import Citation


def lookup(citation: Citation) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT s.id, j.code AS jurisdiction, j.statute_title,
                   s.citation, s.section_number AS section, s.title,
                   s.full_text, s.source_url, s.is_verified, s.scraped_at
            FROM statutes s
            JOIN jurisdictions j ON j.id = s.jurisdiction_id
            WHERE j.code = ? AND s.section_number = ?
            """,
            (citation.jurisdiction, citation.section),
        ).fetchone()
        if not row:
            return None
        result = dict(row)
        result["factors"] = _factors_for(conn, result["id"])
        return result


def _factors_for(conn, statute_id: int) -> list[dict]:
    return [
        dict(r) for r in conn.execute(
            """
            SELECT f.code, f.label, t.confidence, t.tagged_by
            FROM statute_factor_tags t
            JOIN contributing_factors f ON f.id = t.factor_id
            WHERE t.statute_id = ?
            ORDER BY t.confidence DESC
            """,
            (statute_id,),
        )
    ]
