"""Initialize the SQLite database and seed jurisdictions + contributing factors.

Factor codes are loaded from the eval CSV (data/eval-ca-vehicle-code.csv) when present.
Per PRD section 9.4, factor codes must come from the released eval set — we never invent them.
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "legal_harvester.db"
SCHEMA_PATH = ROOT / "db" / "schema.sql"
JURISDICTIONS_PATH = ROOT / "data" / "jurisdictions.json"
EVAL_CSV_PATH = ROOT / "data" / "eval-ca-vehicle-code.csv"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def apply_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text())


def seed_jurisdictions(conn: sqlite3.Connection) -> int:
    if not JURISDICTIONS_PATH.exists():
        return 0
    rows = json.loads(JURISDICTIONS_PATH.read_text())
    conn.executemany(
        """
        INSERT OR IGNORE INTO jurisdictions(code, name, statute_title, base_url)
        VALUES (?, ?, ?, ?)
        """,
        [(r["code"], r["name"], r.get("statute_title"), r.get("base_url")) for r in rows],
    )
    return len(rows)


def _label_to_code(label: str) -> str:
    """Normalise a free-text factor label to UPPER_SNAKE_CASE."""
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", label).strip("_").upper()
    return cleaned or "UNCATEGORIZED"


def _detect_factor_column(fieldnames: list[str]) -> str | None:
    candidates = [
        "contributing_factor", "factor", "factor_label", "category",
        "contributing factor", "Factor", "Category",
    ]
    lower = {f.lower(): f for f in fieldnames}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    return None


def load_factors_from_csv(conn: sqlite3.Connection, csv_path: Path = EVAL_CSV_PATH) -> int:
    """Populate contributing_factors from the eval CSV.

    Returns the number of distinct factors inserted. If the CSV is absent, returns 0.
    """
    if not csv_path.exists():
        print(f"[seed] eval CSV not found at {csv_path}; skipping factor seed.")
        return 0

    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        col = _detect_factor_column(reader.fieldnames or [])
        if not col:
            print(f"[seed] CSV columns: {reader.fieldnames}; no factor column detected.")
            return 0

        labels: list[str] = []
        seen: set[str] = set()
        for row in reader:
            label = (row.get(col) or "").strip()
            if not label or label in seen:
                continue
            seen.add(label)
            labels.append(label)

    inserted = 0
    for label in labels:
        conn.execute(
            """
            INSERT OR IGNORE INTO contributing_factors(code, label)
            VALUES (?, ?)
            """,
            (_label_to_code(label), label),
        )
        inserted += 1
    return inserted


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        apply_schema(conn)
        n_jur = seed_jurisdictions(conn)
        n_fac = load_factors_from_csv(conn)
        conn.commit()
    print(f"Initialized {DB_PATH}")
    print(f"  jurisdictions seeded: {n_jur}")
    print(f"  contributing_factors seeded: {n_fac}")


if __name__ == "__main__":
    main()
