"""Tag each statute with contributing-factor labels using keyword matching against factor labels."""
from __future__ import annotations

from db.seed import connect


def classify_all() -> int:
    tagged = 0
    with connect() as conn:
        factors = conn.execute(
            "SELECT id, code, label FROM contributing_factors"
        ).fetchall()
        # Derive keywords from label words (new schema has no keywords column)
        keyword_index = [
            (f["id"], f["code"], [w.lower() for w in f["label"].split() if len(w) > 3])
            for f in factors
        ]
        statutes = conn.execute("SELECT id, title, full_text FROM statutes").fetchall()
        for s in statutes:
            haystack = f"{s['title'] or ''} {s['full_text'] or ''}".lower()
            for fid, _code, keywords in keyword_index:
                if any(kw in haystack for kw in keywords):
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO statute_factor_tags(statute_id, factor_id, confidence)
                        VALUES (?, ?, ?)
                        """,
                        (s["id"], fid, 1.0),
                    )
                    tagged += 1
        conn.commit()
    return tagged


if __name__ == "__main__":
    print(f"Tagged {classify_all()} statute-factor pairs")
