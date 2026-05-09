"""SQLite FTS5 full-text search over statute bodies."""
from __future__ import annotations

from db.seed import connect


def search(query: str, jurisdiction: str | None = None, limit: int = 20) -> list[dict]:
    # statute_fts columns: citation(0), title(1), full_text(2)
    sql = """
        SELECT s.id,
               j.code           AS jurisdiction,
               j.statute_title  AS code_name,
               s.section_number AS section,
               s.title,
               s.citation,
               snippet(statute_fts, 2, '<b>', '</b>', ' … ', 12) AS snippet,
               bm25(statute_fts) AS rank
        FROM statute_fts
        JOIN statutes s     ON s.id = statute_fts.rowid
        JOIN jurisdictions j ON j.id = s.jurisdiction_id
        WHERE statute_fts MATCH ?
    """
    args: list = [query]
    if jurisdiction:
        sql += " AND j.code = ?"
        args.append(jurisdiction)
    sql += " ORDER BY rank LIMIT ?"
    args.append(limit)

    with connect() as conn:
        return [dict(r) for r in conn.execute(sql, args)]
