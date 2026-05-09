"""Single source of truth for app/runtime settings.

Reads from environment variables and an optional `.env` at repo root.
DB_PATH is deliberately re-exported from db.seed so harvester scripts and the
Streamlit app point at the same database file.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=False)

# DB_PATH lives in db.seed; we re-export so callers have one import surface.
from db.seed import DB_PATH  # noqa: E402

ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL: str = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
SCRAPE_DELAY_SECONDS: float = float(os.environ.get("SCRAPE_DELAY_SECONDS", "1"))

AI_AVAILABLE: bool = bool(ANTHROPIC_API_KEY)
