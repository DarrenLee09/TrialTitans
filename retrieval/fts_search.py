"""SQLite FTS5 full-text search over statute text + title + citation."""
from __future__ import annotations

from db.seed import connect


def search(query: str, jurisdiction: str | None = None, limit: int = 20) -> list[dict]:
    # statute_fts columns: 0=citation, 1=title, 2=full_text — snippet on full_text.
    sql = """
        SELECT s.id, j.code AS jurisdiction, j.statute_title,
               s.citation, s.section_number AS section, s.title,
               s.full_text, s.source_url, s.is_verified,
               snippet(statute_fts, 2, '<b>', '</b>', ' … ', 12) AS snippet,
               bm25(statute_fts) AS rank
        FROM statute_fts
        JOIN statutes s        ON s.id = statute_fts.rowid
        JOIN jurisdictions j   ON j.id = s.jurisdiction_id
        WHERE statute_fts MATCH ?
    """
    args: list = [query]
    if jurisdiction:
        sql += " AND j.code = ?"
        args.append(jurisdiction)
    sql += " ORDER BY rank LIMIT ?"
    args.append(limit)

    with connect() as conn:
        rows = [dict(r) for r in conn.execute(sql, args)]
        for r in rows:
            r["factors"] = _factors_for(conn, r["id"])
        return rows


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
