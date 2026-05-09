"""(Re)populate the statute_fts virtual table from statutes."""
from __future__ import annotations

from db.seed import connect


def rebuild() -> int:
    with connect() as conn:
        conn.execute("INSERT INTO statute_fts(statute_fts) VALUES ('rebuild')")
        conn.commit()
        n = conn.execute("SELECT COUNT(*) AS c FROM statute_fts").fetchone()["c"]
    return n


if __name__ == "__main__":
    print(f"FTS index rebuilt with {rebuild()} rows")
