"""Eval coverage: every citation in eval-ca-vehicle-code.csv must end up in the DB
with at least one contributing-factor tag (PRD §11, hour 0:15–1:00)."""
from __future__ import annotations

import csv

import pytest

from db.seed import connect
from harvester.ingest_csv import (
    DEFAULT_CSV,
    DEFAULT_JURISDICTION,
    _extract_section,
    _resolve_columns,
    ingest,
)
from db import seed as seed_module


def _read_eval_rows() -> list[dict]:
    with DEFAULT_CSV.open(newline="") as f:
        reader = csv.DictReader(f)
        cols = _resolve_columns(reader.fieldnames or [])
        rows = []
        for row in reader:
            citation = (row[cols["citation"]] or "").strip() if cols["citation"] else ""
            if not citation:
                continue
            section = _extract_section(
                citation,
                fallback=row[cols["section_number"]] if cols["section_number"] else None,
            )
            factor = (row[cols["factor"]] or "").strip() if cols["factor"] else ""
            rows.append({"citation": citation, "section": section, "factor": factor})
        return rows


@pytest.fixture(scope="module", autouse=True)
def _seed_and_ingest():
    if not DEFAULT_CSV.exists():
        pytest.skip(f"eval CSV not present at {DEFAULT_CSV}")
    seed_module.main()
    ingest(DEFAULT_CSV, jurisdiction_code=DEFAULT_JURISDICTION)


def test_eval_csv_has_rows():
    rows = _read_eval_rows()
    assert rows, "eval CSV is empty"


def test_every_eval_citation_is_in_db():
    expected = _read_eval_rows()
    with connect() as conn:
        jur = conn.execute(
            "SELECT id FROM jurisdictions WHERE code = ?", (DEFAULT_JURISDICTION,)
        ).fetchone()
        assert jur, "CA jurisdiction missing — run db.seed"
        present = {
            r["section_number"]
            for r in conn.execute(
                "SELECT section_number FROM statutes WHERE jurisdiction_id = ?",
                (jur["id"],),
            )
        }

    missing = [r["section"] for r in expected if r["section"] not in present]
    assert not missing, f"missing {len(missing)} eval statutes: {missing[:10]}"


def test_every_eval_statute_has_a_factor_tag():
    expected = _read_eval_rows()
    with_factor = [r for r in expected if r["factor"]]
    if not with_factor:
        pytest.skip("eval CSV has no contributing-factor column — nothing to assert")

    with connect() as conn:
        jur = conn.execute(
            "SELECT id FROM jurisdictions WHERE code = ?", (DEFAULT_JURISDICTION,)
        ).fetchone()
        tagged_sections = {
            r["section_number"]
            for r in conn.execute(
                """
                SELECT DISTINCT s.section_number
                FROM statutes s
                JOIN statute_factor_tags t ON t.statute_id = s.id
                WHERE s.jurisdiction_id = ?
                """,
                (jur["id"],),
            )
        }

    untagged = [r["section"] for r in with_factor if r["section"] not in tagged_sections]
    assert not untagged, f"{len(untagged)} eval statutes have no tag: {untagged[:10]}"
