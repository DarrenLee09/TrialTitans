"""Load eval-ca-vehicle-code.csv into the statutes table.

Supports both legacy headers (`jurisdiction`, `code`, `section`, `body`, ...)
and the eval CSV headers (`State`, `Universal Citation`, `Section #`,
`Statute Language`, ...).
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from db.seed import connect

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = ROOT / "eval-ca-vehicle-code.csv"

STATE_TO_JURISDICTION = {
    "california": "CA",
}


def _get_first(row: dict[str, str], *keys: str, default: str | None = None) -> str | None:
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        value = value.strip()
        if value:
            return value
    return default


def ingest(csv_path: Path = DEFAULT_CSV) -> int:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    inserted = 0
    with connect() as conn, csv_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            state = _get_first(row, "jurisdiction", "State", default="CA")
            jurisdiction = STATE_TO_JURISDICTION.get((state or "").lower(), state or "CA")
            code_name = _get_first(row, "code", "Universal Citation", default="Vehicle Code")
            section = _get_first(row, "section", "Section #")
            if not section:
                continue
            title = _get_first(row, "title", "Statute")
            body = _get_first(row, "body", "Statute Language", "Complete Statute", default="")
            source_url = _get_first(row, "source_url")
            effective_date = _get_first(row, "effective_date")

            conn.execute(
                """
                INSERT OR REPLACE INTO statutes
                  (jurisdiction, code_name, section, title, body, source_url, effective_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    jurisdiction,
                    code_name,
                    section,
                    title,
                    body,
                    source_url,
                    effective_date,
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
