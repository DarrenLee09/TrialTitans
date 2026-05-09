"""Exact SQL lookup by (jurisdiction, section)."""
from __future__ import annotations

from db.seed import connect
from retrieval.citation_parser import Citation


def lookup(citation: Citation) -> dict | None:
    # Multi-code DBs (CA has 28 codes, NY has 10 laws) need code_name in the
    # filter — otherwise "NY GBL §349" picks up "NY VAT §349" by accident.
    # Use a citation-substring match because stored citations vary in spacing
    # and punctuation across sources ("CA Veh Code §22107" vs "Cal. Veh. Code § 22107").
    code_pattern = f"%{citation.code_name}%"
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
            WHERE j.code = ?
              AND s.section_number = ?
              AND LOWER(s.citation) LIKE LOWER(?)
            LIMIT 1
            """,
            (citation.jurisdiction, citation.section, code_pattern),
        ).fetchone()
        return dict(row) if row else None
