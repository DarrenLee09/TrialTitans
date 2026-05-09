"""Exact SQL lookup by (jurisdiction, section)."""
from __future__ import annotations

from db.seed import connect
from retrieval._tags import attach_factor_tags
from retrieval.citation_parser import Citation

_SELECT = """
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
"""


def lookup(citation: Citation) -> dict | None:
    """Return the matching statute dict or None.

    Tries the user-supplied section_number first (e.g. "2800.1(a)").
    If nothing matches and the user supplied a subsection, falls back to the
    bare section. If they supplied no subsection, falls back to the first
    "<section>(...)"-style row, since CSVs sometimes only carry the
    fully-qualified section_number.
    """
    full_section = citation.section + (citation.subsection or "")
    with connect() as conn:
        row = conn.execute(_SELECT, (citation.jurisdiction, full_section)).fetchone()
        if row is None and citation.subsection:
            row = conn.execute(_SELECT, (citation.jurisdiction, citation.section)).fetchone()
        if row is None and not citation.subsection:
            row = conn.execute(
                _SELECT.replace("s.section_number = ?", "s.section_number LIKE ?"),
                (citation.jurisdiction, f"{citation.section}(%"),
            ).fetchone()
        if row is None:
            return None
        result = [dict(row)]
        attach_factor_tags(conn, result)
        return result[0]
