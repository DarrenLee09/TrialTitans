"""Exact SQL lookup by (jurisdiction, section)."""
from __future__ import annotations

from db.seed import connect
from retrieval.citation_parser import Citation


def lookup(citation: Citation) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT s.id,
                   j.code           AS jurisdiction,
                   j.statute_title  AS code_name,
                   s.section_number AS section,
                   s.title,
                   s.full_text      AS body,
                   s.citation,
                   s.source_url
            FROM statutes s
            JOIN jurisdictions j ON j.id = s.jurisdiction_id
            WHERE j.code = ? AND s.section_number = ?
            """,
            (citation.jurisdiction, citation.section),
        ).fetchone()
        return dict(row) if row else None
