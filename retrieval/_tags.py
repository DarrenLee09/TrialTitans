"""Shared helper: attach contributing-factor tags to retrieval result rows.

All retrieval modules (exact_lookup, factor_search, fts_search, vector_search)
return statute dicts. The frontend result_card expects each dict to carry a
`factors` field describing how Claude or a human classified it. This helper
runs ONE query per call to avoid N+1 lookups.
"""
from __future__ import annotations

import sqlite3


def attach_factor_tags(conn: sqlite3.Connection, rows: list[dict]) -> list[dict]:
    """Mutate `rows` to add a `factors` list on each one. Returns the same list.

    Each factor entry is `{code, label, confidence, tagged_by}`.
    Statutes with no tags get an empty list.
    """
    if not rows:
        return rows

    statute_ids = [r["id"] for r in rows if r.get("id") is not None]
    if not statute_ids:
        for r in rows:
            r.setdefault("factors", [])
        return rows

    placeholders = ",".join("?" * len(statute_ids))
    sql = f"""
        SELECT t.statute_id, f.code, f.label, t.confidence, t.tagged_by
        FROM statute_factor_tags t
        JOIN contributing_factors f ON f.id = t.factor_id
        WHERE t.statute_id IN ({placeholders})
        ORDER BY t.confidence DESC, f.label
    """
    by_statute: dict[int, list[dict]] = {sid: [] for sid in statute_ids}
    for row in conn.execute(sql, statute_ids):
        by_statute[row["statute_id"]].append({
            "code":       row["code"],
            "label":      row["label"],
            "confidence": row["confidence"],
            "tagged_by":  row["tagged_by"],
        })

    for r in rows:
        r["factors"] = by_statute.get(r.get("id"), [])
    return rows
