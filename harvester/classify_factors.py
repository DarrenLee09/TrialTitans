"""Tag each statute with contributing-factor labels using keyword matching against factors.keywords."""
from __future__ import annotations

import json

from db.seed import connect


def classify_all() -> int:
    tagged = 0
    with connect() as conn:
        factors = conn.execute("SELECT id, slug, keywords FROM factors").fetchall()
        keyword_index = [
            (f["id"], f["slug"], json.loads(f["keywords"] or "[]")) for f in factors
        ]
        statutes = conn.execute("SELECT id, title, body FROM statutes").fetchall()
        for s in statutes:
            haystack = f"{s['title'] or ''} {s['body'] or ''}".lower()
            for fid, _slug, keywords in keyword_index:
                if any(kw.lower() in haystack for kw in keywords):
                    conn.execute(
                        "INSERT OR IGNORE INTO statute_factors(statute_id, factor_id, confidence) VALUES (?, ?, ?)",
                        (s["id"], fid, 1.0),
                    )
                    tagged += 1
        conn.commit()
    return tagged


if __name__ == "__main__":
    print(f"Tagged {classify_all()} statute-factor pairs")
