"""Search statutes by contributing factor (DUI, failure to yield, etc.)."""
from __future__ import annotations

from db.seed import connect


def list_factors() -> list[dict]:
    with connect() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT code, label FROM contributing_factors ORDER BY label"
        )]


def by_factor(code: str, jurisdiction: str | None = None, limit: int = 50) -> list[dict]:
    sql = """
        SELECT s.id,
               j.code           AS jurisdiction,
               j.statute_title  AS code_name,
               s.section_number AS section,
               s.title,
               s.full_text      AS body,
               s.citation,
               s.source_url
        FROM statutes s
        JOIN jurisdictions j         ON j.id = s.jurisdiction_id
        JOIN statute_factor_tags sf  ON sf.statute_id = s.id
        JOIN contributing_factors f  ON f.id = sf.factor_id
        WHERE f.code = ?
    """
    args: list = [code]
    if jurisdiction:
        sql += " AND j.code = ?"
        args.append(jurisdiction)
    sql += " ORDER BY sf.confidence DESC LIMIT ?"
    args.append(limit)

    with connect() as conn:
        return [dict(r) for r in conn.execute(sql, args)]
