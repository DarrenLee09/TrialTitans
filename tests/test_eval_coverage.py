"""Smoke test: when data/eval-ca-vehicle-code.csv is present, ingest covers every row."""
from pathlib import Path

import pytest

from db.seed import connect
from harvester.ingest_csv import DEFAULT_CSV, ingest


@pytest.mark.skipif(not DEFAULT_CSV.exists(), reason="eval CSV not provided")
def test_ingest_loads_all_rows():
    n = ingest(DEFAULT_CSV)
    with connect() as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM statutes").fetchone()["c"]
    assert count >= n > 0
