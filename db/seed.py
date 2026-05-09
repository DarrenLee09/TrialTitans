"""Initialize the SQLite database from schema.sql and seed jurisdictions + factors."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "legal_harvester.db"
SCHEMA_PATH = ROOT / "db" / "schema.sql"
JURISDICTIONS_PATH = ROOT / "data" / "jurisdictions.json"


DEFAULT_FACTORS = [
    ("dui",                "Driving under the influence",      ["dui", "drunk", "intoxicated", "alcohol", "bac"]),
    ("failure_to_yield",   "Failure to yield",                  ["yield", "right of way"]),
    ("speeding",           "Speeding / unsafe speed",           ["speed", "speeding", "too fast"]),
    ("distracted_driving", "Distracted driving",                ["phone", "texting", "distracted"]),
    ("following_too_close","Following too closely",             ["tailgating", "following too close"]),
    ("unsafe_lane_change", "Unsafe lane change",                ["lane change", "merge", "swerve"]),
    ("running_red_light",  "Running red light or stop sign",    ["red light", "stop sign", "ran the light"]),
    ("reckless_driving",   "Reckless driving",                  ["reckless", "wanton"]),
]


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def apply_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text())


def seed_jurisdictions(conn: sqlite3.Connection) -> None:
    if not JURISDICTIONS_PATH.exists():
        return
    rows = json.loads(JURISDICTIONS_PATH.read_text())
    conn.executemany(
        "INSERT OR IGNORE INTO jurisdictions(code, name, country) VALUES (?, ?, ?)",
        [(r["code"], r["name"], r.get("country", "US")) for r in rows],
    )


def seed_factors(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "INSERT OR IGNORE INTO factors(slug, label, keywords) VALUES (?, ?, ?)",
        [(slug, label, json.dumps(kw)) for slug, label, kw in DEFAULT_FACTORS],
    )


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        apply_schema(conn)
        seed_jurisdictions(conn)
        seed_factors(conn)
        conn.commit()
    print(f"Initialized {DB_PATH}")


if __name__ == "__main__":
    main()
