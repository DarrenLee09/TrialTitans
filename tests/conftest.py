"""Shared pytest fixtures: build an isolated SQLite DB per test session."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session", autouse=True)
def _isolated_db(tmp_path_factory):
    """Point db.seed at a tmp DB so tests never clobber the real one."""
    from db import seed

    tmp = tmp_path_factory.mktemp("trialtitans") / "test.db"
    seed.DB_PATH = tmp
    seed.main()
    yield
