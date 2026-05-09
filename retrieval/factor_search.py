"""Search statutes by contributing factor (DUI, failure to yield, etc.)."""
from __future__ import annotations

from db.seed import connect


def list_factors() -> list[dict]:
    with connect() as conn:
        return [
            dict(r) for r in conn.execute(
                "SELECT code, label FROM contributing_factors ORDER BY label"
            )
        ]


def by_factor(code: str, jurisdiction: str | None = None, limit: int = 50) -> list[dict]:
    sql = """
        SELECT s.id, j.code AS jurisdiction, j.statute_title,
               s.citation, s.section_number AS section, s.title,
               s.full_text, s.source_url, s.is_verified,
               t.confidence, t.tagged_by
        FROM statutes s
        JOIN jurisdictions j           ON j.id = s.jurisdiction_id
        JOIN statute_factor_tags t     ON t.statute_id = s.id
        JOIN contributing_factors f    ON f.id = t.factor_id
        WHERE f.code = ?
    """
    args: list = [code]
    if jurisdiction:
        sql += " AND j.code = ?"
        args.append(jurisdiction)
    sql += " ORDER BY t.confidence DESC LIMIT ?"
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
