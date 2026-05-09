"""(Re)populate the statute_fts virtual table from statutes."""
from __future__ import annotations

from db.seed import connect


def rebuild() -> int:
    with connect() as conn:
        conn.execute("DELETE FROM statute_fts")
        conn.execute(
            """
            INSERT INTO statute_fts(rowid, title, body, section, jurisdiction)
            SELECT id, COALESCE(title, ''), body, section, jurisdiction FROM statutes
            """
        )
        conn.commit()
        n = conn.execute("SELECT COUNT(*) AS c FROM statute_fts").fetchone()["c"]
    return n


if __name__ == "__main__":
    print(f"FTS index rebuilt with {rebuild()} rows")
