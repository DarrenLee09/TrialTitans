"""SQLite FTS5 full-text search over statute bodies."""
from __future__ import annotations

import re

from db.seed import connect
from retrieval._tags import attach_factor_tags


def _sanitize_fts_query(query: str) -> str:
    """Convert free-form text to a safe FTS5 MATCH expression.

    FTS5 treats characters like `-`, `:`, `*`, `(`, `)`, `"` as operators or
    column refs. For natural-language queries we strip them, then quote each
    remaining word so any incidental punctuation can't break the parser.
    Empty input returns a sentinel that matches nothing.
    """
    cleaned = re.sub(r"[^A-Za-z0-9\s]", " ", query)
    tokens = [t for t in cleaned.split() if t]
    if not tokens:
        return '""'
    # Phrase-quote each token; OR-join allows partial matches.
    return " OR ".join(f'"{t}"' for t in tokens)


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
    args: list = [_sanitize_fts_query(query)]
    if jurisdiction:
        sql += " AND j.code = ?"
        args.append(jurisdiction)
    sql += " ORDER BY rank LIMIT ?"
    args.append(limit)

    with connect() as conn:
        rows = [dict(r) for r in conn.execute(sql, args)]
        attach_factor_tags(conn, rows)
        return rows
