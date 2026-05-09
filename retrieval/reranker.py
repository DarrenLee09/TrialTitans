"""Claude-powered reranker that also produces a per-result attorney rationale.

Single Claude call → JSON `[{"id": int, "why": "1-2 sentences"}]`.
Each result gets a `explanation` field consumed by the result card.

If the Anthropic SDK or API key is missing, this falls back to a no-op slice.
"""
from __future__ import annotations

import json
import os

try:
    from anthropic import Anthropic
except ImportError:  # anthropic SDK is optional at runtime
    Anthropic = None  # type: ignore

MODEL = "claude-sonnet-4-6"


def rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    if not candidates:
        return []
    if Anthropic is None or not os.environ.get("ANTHROPIC_API_KEY"):
        return candidates[:top_k]

    try:
        ranking = _ask_claude(query, candidates)
    except Exception:
        return candidates[:top_k]
    return _apply_order(candidates, ranking, top_k)


def _apply_order(
    candidates: list[dict],
    ranking: list[dict],
    top_k: int,
) -> list[dict]:
    """Reorder `candidates` per `ranking` and tag each with an explanation.

    `ranking` is `[{"id": int, "why": str}, ...]` from Claude. Unknown ids and
    duplicates are skipped. If `ranking` produces no usable entries, falls back
    to the input order.
    """
    by_id = {c["id"]: c for c in candidates}
    out: list[dict] = []
    seen: set = set()
    for entry in ranking:
        sid = entry.get("id")
        if sid is None or sid in seen or sid not in by_id:
            continue
        seen.add(sid)
        enriched = dict(by_id[sid])
        enriched["explanation"] = str(entry.get("why") or "")
        out.append(enriched)
        if len(out) >= top_k:
            break
    if not out:
        return candidates[:top_k]
    return out


_SYSTEM = """\
You rerank statute candidates by relevance to a plaintiff-side personal-injury
attorney's research question.

Reply with ONLY a JSON array of objects, no prose:
  [{"id": <int>, "why": "<1-2 sentence rationale>"}, ...]

Order best-first. The "why" should explain in attorney-useful terms why the
statute is on point — what element it satisfies, what it requires/prohibits,
why it matches the question. Quote the statute's section number when natural.
Skip statutes that are not relevant.
"""


def _ask_claude(query: str, candidates: list[dict]) -> list[dict]:
    client = Anthropic()
    payload = [
        {
            "id": c["id"],
            "section": c.get("section"),
            "title": c.get("title"),
            "snippet": c.get("snippet") or (c.get("body") or c.get("full_text") or "")[:500],
        }
        for c in candidates
    ]
    msg = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Question: {query}\n\nCandidates:\n{json.dumps(payload, indent=2)}",
        }],
    )
    text = msg.content[0].text.strip() if msg.content else "[]"
    parsed = json.loads(text)
    if not isinstance(parsed, list):
        return []
    return [e for e in parsed if isinstance(e, dict) and "id" in e]
