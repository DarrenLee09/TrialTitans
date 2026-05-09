"""Generate attorney-friendly natural-language answers from retrieved statutes."""
from __future__ import annotations

import os

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None  # type: ignore

from ai.prompts import (
    ATTORNEY_ANSWER_SYSTEM,
    ATTORNEY_ANSWER_USER_TEMPLATE,
    render_statutes_block,
)

MODEL = "claude-opus-4-7"


def answer(question: str, statutes: list[dict], jurisdiction: str | None = None) -> str:
    if Anthropic is None or not os.environ.get("ANTHROPIC_API_KEY"):
        return _offline_fallback(question, statutes)

    client = Anthropic()
    user = ATTORNEY_ANSWER_USER_TEMPLATE.format(
        question=question,
        jurisdiction=jurisdiction or "any",
        statutes_block=render_statutes_block(statutes),
    )
    msg = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=ATTORNEY_ANSWER_SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text if msg.content else ""


def _offline_fallback(question: str, statutes: list[dict]) -> str:
    if not statutes:
        return "(No statutes retrieved; set ANTHROPIC_API_KEY for AI synthesis.)"
    lines = [f"Question: {question}", "", "Top statutes:"]
    for s in statutes[:5]:
        cite = f"{s.get('jurisdiction')} {s.get('code_name')} § {s.get('section')}"
        lines.append(f"- {cite}: {s.get('title') or (s.get('body') or '')[:120]}")
    return "\n".join(lines)
