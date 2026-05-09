"""Exact SQL lookup by (jurisdiction, code, section)."""
from __future__ import annotations

from db.seed import connect
from retrieval.citation_parser import Citation


def lookup(citation: Citation) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT id, jurisdiction, code_name, section, title, body, source_url, effective_date
            FROM statutes
            WHERE jurisdiction = ? AND code_name = ? AND section = ?
            """,
            (citation.jurisdiction, citation.code_name, citation.section),
        ).fetchone()
        return dict(row) if row else None
