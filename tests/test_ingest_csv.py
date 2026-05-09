"""Tests for harvester.ingest_csv."""
from __future__ import annotations

import pytest

from db.seed import connect

# Slugs of factors seeded by db.seed.DEFAULT_FACTORS. The reset fixture preserves
# these and deletes anything else, so per-test auto-create counts are deterministic
# regardless of which other test files ran first.
SEEDED_SLUGS = (
    "dui", "failure_to_yield", "speeding", "distracted_driving",
    "following_too_close", "unsafe_lane_change", "running_red_light",
    "reckless_driving",
)


@pytest.fixture(autouse=True)
def _reset_ingest_state():
    """Each test starts with empty statutes/statute_factors and only the
    8 seeded factors. Auto-created factors from prior tests are removed."""
    with connect() as conn:
        conn.execute("DELETE FROM statute_factors")
        conn.execute("DELETE FROM statutes")
        placeholders = ",".join("?" * len(SEEDED_SLUGS))
        conn.execute(
            f"DELETE FROM factors WHERE slug NOT IN ({placeholders})",
            SEEDED_SLUGS,
        )
        conn.commit()
    yield


def test_slugify_basic():
    from harvester.ingest_csv import slugify
    assert slugify("Improper Turning") == "improper_turning"


def test_slugify_punctuation():
    from harvester.ingest_csv import slugify
    assert slugify("DUI/DWI") == "dui_dwi"


def test_slugify_collapses_runs_and_strips_edges():
    from harvester.ingest_csv import slugify
    assert slugify("  Failure -- to  Yield!  ") == "failure_to_yield"
