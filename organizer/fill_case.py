"""Organizer agent — fills the CA PI doctrine template from harvested statutes
and the attorney's case description."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import TypedDict

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None  # type: ignore

from db.seed import connect
from organizer.prompts import (
    ORGANIZER_SYSTEM,
    ORGANIZER_USER_TEMPLATE,
    render_statutes_block,
)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "docs" / "case_doctrine_template.md"


class FilledCase(TypedDict):
    summary: str
    filled_markdown: str
    gap_report: list[dict]
    statutes_used: list[dict]
    used_ai: bool


def fill_case(
    case_description: str,
    statutes: list[dict],
    jurisdiction: str | None = None,
) -> FilledCase:
    """Fill the doctrine template for a CA motor-vehicle PI case.

    Inputs:
      case_description: attorney's free-form fact pattern.
      statutes: Harvester result rows. Each may have either `body` or `snippet`
        depending on which retrieval path produced it. We re-fetch full bodies
        so the model always sees the same shape.
      jurisdiction: optional 2-letter code to scope the answer.
    """
    statutes_full = _hydrate_statutes(statutes)

    if Anthropic is None or not os.environ.get("ANTHROPIC_API_KEY"):
        return _offline_fallback(case_description, statutes_full, jurisdiction)

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    user = ORGANIZER_USER_TEMPLATE.format(
        case_description=case_description.strip() or "(none provided)",
        jurisdiction=jurisdiction or "any",
        statutes_block=render_statutes_block(statutes_full),
        template=template,
    )

    client = Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=ORGANIZER_SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    raw = msg.content[0].text if msg.content else ""

    summary = _extract_tag(raw, "SUMMARY") or "(no summary returned)"
    filled = _extract_tag(raw, "FILLED_TEMPLATE") or template
    gaps_raw = _extract_tag(raw, "GAP_REPORT") or "[]"
    try:
        gap_report = json.loads(gaps_raw)
        if not isinstance(gap_report, list):
            gap_report = []
    except json.JSONDecodeError:
        gap_report = []

    return {
        "summary": summary.strip(),
        "filled_markdown": filled.strip(),
        "gap_report": gap_report,
        "statutes_used": statutes_full,
        "used_ai": True,
    }


def _hydrate_statutes(statutes: list[dict]) -> list[dict]:
    """Normalize retrieval shapes — fetch full bodies and source URLs by id."""
    if not statutes:
        return []
    ids = [s["id"] for s in statutes if s.get("id") is not None]
    if not ids:
        return statutes

    placeholders = ",".join("?" for _ in ids)
    sql = f"""
        SELECT s.id,
               j.code           AS jurisdiction,
               j.statute_title  AS code_name,
               s.section_number AS section,
               s.title,
               s.full_text      AS body,
               s.citation,
               s.source_url
        FROM statutes s
        JOIN jurisdictions j ON j.id = s.jurisdiction_id
        WHERE s.id IN ({placeholders})
    """
    with connect() as conn:
        rows = {r["id"]: dict(r) for r in conn.execute(sql, ids)}

    return [rows[i] for i in ids if i in rows]


_TAG_RE_CACHE: dict[str, re.Pattern[str]] = {}


def _extract_tag(text: str, tag: str) -> str | None:
    pattern = _TAG_RE_CACHE.get(tag)
    if pattern is None:
        pattern = re.compile(rf"<{tag}>(.*?)</{tag}>", re.DOTALL)
        _TAG_RE_CACHE[tag] = pattern
    m = pattern.search(text)
    return m.group(1) if m else None


def _offline_fallback(
    case_description: str,
    statutes: list[dict],
    jurisdiction: str | None,
) -> FilledCase:
    """No-API stub — emits the template verbatim with a note and a stub gap report.

    Useful for tests and for running the demo without ANTHROPIC_API_KEY."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    cite_lines = "\n".join(
        f"- {s.get('citation')} ({s.get('source_url', '')})"
        for s in statutes[:5]
    ) or "(none retrieved)"

    summary = (
        "Offline mode — set ANTHROPIC_API_KEY to populate the template. "
        f"Case description: {case_description.strip()[:200] or '(none)'}. "
        f"Top retrieved statutes:\n{cite_lines}"
    )

    filled = (
        f"> **Offline mode.** No ANTHROPIC_API_KEY set — template is shown unfilled. "
        f"Retrieved {len(statutes)} statute(s) for jurisdiction "
        f"{jurisdiction or 'any'}.\n\n"
        f"{template}"
    )

    gap_report = [
        {
            "bucket": "liability",
            "field": "cited_statutes",
            "leverage_tier": 1,
            "closeable": "yes",
            "closing_action": "Set ANTHROPIC_API_KEY and re-run.",
            "status": "open",
        }
    ]

    return {
        "summary": summary,
        "filled_markdown": filled,
        "gap_report": gap_report,
        "statutes_used": statutes,
        "used_ai": False,
    }
