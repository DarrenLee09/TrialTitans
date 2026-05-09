"""Search statutes by contributing factor (DUI, failure to yield, etc.)."""
from __future__ import annotations

from db.seed import connect


def list_factors() -> list[dict]:
    with connect() as conn:
        return [dict(r) for r in conn.execute("SELECT slug, label FROM factors ORDER BY label")]


def by_factor(slug: str, jurisdiction: str | None = None, limit: int = 50) -> list[dict]:
    sql = """
        SELECT s.id, s.jurisdiction, s.code_name, s.section, s.title, s.body, s.source_url
        FROM statutes s
        JOIN statute_factors sf ON sf.statute_id = s.id
        JOIN factors f          ON f.id = sf.factor_id
        WHERE f.slug = ?
    """
    args: list = [slug]
    if jurisdiction:
        sql += " AND s.jurisdiction = ?"
        args.append(jurisdiction)
    sql += " ORDER BY sf.confidence DESC LIMIT ?"
    args.append(limit)

    with connect() as conn:
        return [dict(r) for r in conn.execute(sql, args)]
