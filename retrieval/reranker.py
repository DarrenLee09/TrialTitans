"""Optional Claude-based reranker for FTS results."""
from __future__ import annotations

import json
import os

try:
    from anthropic import Anthropic
except ImportError:  # anthropic SDK is optional at runtime
    Anthropic = None  # type: ignore

MODEL = "claude-opus-4-7"


def rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    if not candidates or Anthropic is None or not os.environ.get("ANTHROPIC_API_KEY"):
        return candidates[:top_k]

    client = Anthropic()
    payload = [
        {"id": c["id"], "section": c.get("section"), "title": c.get("title"),
         "snippet": c.get("snippet") or (c.get("body") or "")[:500]}
        for c in candidates
    ]
    msg = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=(
            "You rerank statute candidates by relevance to the user's question. "
            "Reply with ONLY a JSON array of statute ids in best-first order."
        ),
        messages=[{
            "role": "user",
            "content": f"Question: {query}\n\nCandidates:\n{json.dumps(payload, indent=2)}",
        }],
    )

    try:
        order = json.loads(msg.content[0].text.strip())
    except (json.JSONDecodeError, AttributeError, IndexError):
        return candidates[:top_k]

    by_id = {c["id"]: c for c in candidates}
    ranked = [by_id[i] for i in order if i in by_id]
    return ranked[:top_k] if ranked else candidates[:top_k]
