"""Smoke tests for the Organizer agent."""
from __future__ import annotations

import os

from db.seed import connect
from organizer import fill_case as organizer
from organizer.fill_case import _extract_tag, _hydrate_statutes


def _insert_statute(jurisdiction_code: str, section: str, body: str) -> int:
    with connect() as conn:
        jur_id = conn.execute(
            "SELECT id FROM jurisdictions WHERE code = ?", (jurisdiction_code,)
        ).fetchone()["id"]
        cur = conn.execute(
            """
            INSERT INTO statutes(jurisdiction_id, citation, section_number, title, full_text, source_url)
            VALUES (?, ?, ?, '', ?, 'https://example.com/source')
            """,
            (jur_id, f"{jurisdiction_code} Veh Code §{section}", section, body),
        )
        conn.commit()
        return cur.lastrowid


def test_extract_tag_roundtrip():
    raw = "<SUMMARY>Hi there.</SUMMARY>\n<GAP_REPORT>[]</GAP_REPORT>"
    assert _extract_tag(raw, "SUMMARY") == "Hi there."
    assert _extract_tag(raw, "GAP_REPORT") == "[]"
    assert _extract_tag(raw, "MISSING") is None


def test_hydrate_statutes_pulls_full_body():
    sid = _insert_statute(
        "CA", "99001", "Test text — failure to yield at intersection causing collision."
    )
    raw = [{"id": sid, "snippet": "…fragment…"}]
    full = _hydrate_statutes(raw)
    assert len(full) == 1
    assert full[0]["body"].startswith("Test text")
    assert full[0]["source_url"] == "https://example.com/source"
    assert full[0]["jurisdiction"] == "CA"


def test_offline_fallback_returns_filled_case_shape(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    sid = _insert_statute(
        "CA", "99002", "Driver shall yield right-of-way to pedestrians in crosswalk."
    )

    result = organizer.fill_case(
        case_description="Pedestrian struck in crosswalk; driver did not yield.",
        statutes=[{"id": sid}],
        jurisdiction="CA",
    )

    assert result["used_ai"] is False
    assert "summary" in result and result["summary"]
    assert "filled_markdown" in result and "Doctrine Template" in result["filled_markdown"]
    assert isinstance(result["gap_report"], list)
    assert result["statutes_used"][0]["id"] == sid
