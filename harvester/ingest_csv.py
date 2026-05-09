"""Load eval-ca-vehicle-code.csv into the statutes table.

Expected columns (best-effort; missing ones are tolerated):
    jurisdiction, code, section, title, body, source_url, effective_date
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from db.seed import connect

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = ROOT / "data" / "eval-ca-vehicle-code.csv"


def slugify(label: str) -> str:
    """lowercase → replace non-alnum runs with `_` → strip leading/trailing `_`."""
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


def ingest(csv_path: Path = DEFAULT_CSV) -> int:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    inserted = 0
    with connect() as conn, csv_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            conn.execute(
                """
                INSERT OR REPLACE INTO statutes
                  (jurisdiction, code_name, section, title, body, source_url, effective_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.get("jurisdiction", "CA"),
                    row.get("code", "Vehicle Code"),
                    row["section"],
                    row.get("title"),
                    row.get("body", ""),
                    row.get("source_url"),
                    row.get("effective_date"),
                ),
            )
            inserted += 1
        conn.commit()
    return inserted


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    args = ap.parse_args()
    n = ingest(args.csv)
    print(f"Ingested {n} rows from {args.csv}")


if __name__ == "__main__":
    main()
