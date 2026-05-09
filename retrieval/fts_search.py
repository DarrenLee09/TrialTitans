"""SQLite FTS5 full-text search over statute bodies."""
from __future__ import annotations

from db.seed import connect


def search(query: str, jurisdiction: str | None = None, limit: int = 20) -> list[dict]:
    sql = """
        SELECT s.id, s.jurisdiction, s.code_name, s.section, s.title,
               snippet(statute_fts, 1, '<b>', '</b>', ' … ', 12) AS snippet,
               bm25(statute_fts) AS rank
        FROM statute_fts
        JOIN statutes s ON s.id = statute_fts.rowid
        WHERE statute_fts MATCH ?
    """
    args: list = [query]
    if jurisdiction:
        sql += " AND s.jurisdiction = ?"
        args.append(jurisdiction)
    sql += " ORDER BY rank LIMIT ?"
    args.append(limit)

    with connect() as conn:
        return [dict(r) for r in conn.execute(sql, args)]
