"""Natural-language query interpreter.

Turns "DUI cases in Florida involving school zones" into:
    {
      "jurisdictions": ["FL"],
      "factors": ["DUI_DWI"],
      "intent": "school zones",
    }

Two backends:
    1. Claude (JSON mode) when ANTHROPIC_API_KEY is set — handles paraphrase,
       multi-state ("California vs Texas"), implied factors ("ran a red light").
    2. Offline keyword fallback — exact word/phrase match against the supplied
       jurisdictions + factor labels. Always available; used in tests and any
       runtime missing the key.

The interpreter is the entry point for hybrid retrieval (Phase 5 item 19):
the router uses `jurisdictions` to filter, `factors` to call factor_search,
and `intent` as the FTS / vector-search query.
"""
from __future__ import annotations

import json
import os
import re

try:
    from anthropic import Anthropic
except ImportError:  # anthropic SDK is optional at runtime
    Anthropic = None  # type: ignore

MODEL = "claude-sonnet-4-6"

_FILLER_TOKENS = {
    "in", "about", "for", "involving", "on", "regarding", "concerning",
    "of", "at", "by", "with",
}

# Stopwords skipped when tokenizing factor labels — keeps "to" in
# "Failure to Maintain Lane" from matching every query that contains "to".
_LABEL_STOPWORDS = {
    "to", "a", "an", "the", "of", "in", "on", "at", "for", "with", "by",
    "from", "and", "or", "too", "as",
}
_LABEL_TOKEN_MIN_LEN = 4


def _label_tokens(label: str) -> list[str]:
    """Split "DUI/DWI" → ["DUI", "DWI"]; "Failure to Maintain Lane" → ["Failure", "Maintain", "Lane"].

    Only emits tokens long enough to be meaningful and not in the stopword list.
    Note: 3-letter acronyms like "DUI" are intentionally allowed even though
    they're below the min length — uppercase tokens are kept verbatim.
    """
    parts = re.split(r"[/\s,&\-]+", label)
    out: list[str] = []
    for p in parts:
        if not p:
            continue
        if p.lower() in _LABEL_STOPWORDS:
            continue
        # Keep all-caps acronyms (DUI, DWI, BAC) regardless of length.
        if p.isupper():
            out.append(p)
        elif len(p) >= _LABEL_TOKEN_MIN_LEN:
            out.append(p)
    return out


def _strip_filler(text: str) -> str:
    """Drop short connector words at the start and end of `text`.

    These appear after we strip jurisdictions/factors out of the middle of a
    sentence — "DUI cases in Florida" → "DUI cases in" → "DUI cases".
    """
    tokens = text.split()
    while tokens and tokens[0].lower() in _FILLER_TOKENS:
        tokens.pop(0)
    while tokens and tokens[-1].lower() in _FILLER_TOKENS:
        tokens.pop()
    return " ".join(tokens)


def interpret(
    query: str,
    *,
    jurisdictions: list[tuple[str, str]] | None = None,
    factors: list[tuple[str, str]] | None = None,
) -> dict:
    """Return {jurisdictions, factors, intent}.

    jurisdictions: list of (code, name) tuples — e.g. [("CA", "California")]
    factors:       list of (code, label) tuples — e.g. [("DUI_DWI", "DUI/DWI")]
    """
    if jurisdictions is None:
        jurisdictions = _load_jurisdictions()
    if factors is None:
        factors = _load_factors()

    if Anthropic is not None and os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return _interpret_with_claude(query, jurisdictions, factors)
        except Exception:
            # Any Claude/JSON failure falls back to the deterministic path.
            pass

    return _interpret_offline(query, jurisdictions, factors)


def _load_jurisdictions() -> list[tuple[str, str]]:
    from db.seed import connect

    with connect() as conn:
        return [(r["code"], r["name"]) for r in conn.execute(
            "SELECT code, name FROM jurisdictions ORDER BY code"
        )]


def _load_factors() -> list[tuple[str, str]]:
    from db.seed import connect

    with connect() as conn:
        return [(r["code"], r["label"]) for r in conn.execute(
            "SELECT code, label FROM contributing_factors ORDER BY code"
        )]


def _interpret_offline(
    query: str,
    jurisdictions: list[tuple[str, str]],
    factors: list[tuple[str, str]],
) -> dict:
    text = query
    matched_jurs: list[str] = []
    seen_jur: set[str] = set()

    # Match longer phrases first so "New York" beats "NY" inside the same query.
    juris_patterns = sorted(
        ((code, name) for code, name in jurisdictions),
        key=lambda x: -len(x[1]),
    )
    for code, name in juris_patterns:
        if code in seen_jur:
            continue
        # Full name first (case-insensitive), then code (case-sensitive — codes
        # like "CA" are too short to safely match without case to discriminate).
        name_pat = rf"\b{re.escape(name)}\b"
        if re.search(name_pat, text, re.IGNORECASE):
            matched_jurs.append(code)
            seen_jur.add(code)
            text = re.sub(name_pat, " ", text, flags=re.IGNORECASE)
        code_pat = rf"\b{re.escape(code)}\b"
        if re.search(code_pat, text):  # case-sensitive
            if code not in seen_jur:
                matched_jurs.append(code)
                seen_jur.add(code)
            text = re.sub(code_pat, " ", text)

    # Build an index of tokens UNIQUE to one factor — so "Driving" (in many
    # labels) won't trigger a match, but "DUI" (only in DUI/DWI) will.
    token_owners: dict[str, set[str]] = {}
    for code, label in factors:
        for tok in _label_tokens(label):
            token_owners.setdefault(tok.lower(), set()).add(code)
    unique_tokens: dict[str, str] = {
        tok: next(iter(codes)) for tok, codes in token_owners.items() if len(codes) == 1
    }

    matched_factors: list[str] = []
    seen_fac: set[str] = set()
    factor_patterns = sorted(factors, key=lambda x: -len(x[1]))
    for code, label in factor_patterns:
        if code in seen_fac:
            continue
        # First try the literal label as a whole phrase ("Reckless Driving").
        pat = rf"\b{re.escape(label)}\b"
        if re.search(pat, text, re.IGNORECASE):
            matched_factors.append(code)
            seen_fac.add(code)
            text = re.sub(pat, " ", text, flags=re.IGNORECASE)
            continue
        # Then try each meaningful token in the label, but only if the token
        # is unique to this factor ("DUI" inside "DUI/DWI", but not "Driving"
        # which appears in many labels).
        for tok in _label_tokens(label):
            if unique_tokens.get(tok.lower()) != code:
                continue
            tok_pat = rf"\b{re.escape(tok)}\b"
            if re.search(tok_pat, text, re.IGNORECASE):
                matched_factors.append(code)
                seen_fac.add(code)
                text = re.sub(tok_pat, " ", text, flags=re.IGNORECASE)
                break

    intent = _strip_filler(re.sub(r"\s+", " ", text).strip())

    return {
        "jurisdictions": matched_jurs,
        "factors": matched_factors,
        "intent": intent,
    }


_CLAUDE_SYSTEM = """\
You parse legal-research queries into structured filters.

Reply with ONLY a JSON object, no prose. Schema:
{
  "jurisdictions": ["CA", "FL", ...],   // 2-letter codes from the supplied list
  "factors":       ["DUI_DWI", ...],    // codes from the supplied list
  "intent":        "..."                // remaining keywords for full-text search
}

Rules:
- Use ONLY codes from the supplied lists; do not invent new ones.
- If the query mentions a state by full name ("Florida"), output its code ("FL").
- If a contributing-factor concept is implied ("ran a red light", "drunk driver"),
  pick the closest matching factor code.
- Strip matched jurisdictions and factor names from the intent. Keep the rest
  verbatim. If nothing remains, return "" for intent.
- jurisdictions and factors must be JSON arrays even when empty.
"""


def _interpret_with_claude(
    query: str,
    jurisdictions: list[tuple[str, str]],
    factors: list[tuple[str, str]],
) -> dict:
    client = Anthropic()
    user = (
        f"Query: {query}\n\n"
        f"Available jurisdictions:\n"
        + "\n".join(f"  {c}: {n}" for c, n in jurisdictions)
        + "\n\nAvailable factors:\n"
        + "\n".join(f"  {c}: {l}" for c, l in factors)
    )
    msg = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=_CLAUDE_SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    text = msg.content[0].text.strip() if msg.content else "{}"
    parsed = json.loads(text)

    jur_codes = {c for c, _ in jurisdictions}
    fac_codes = {c for c, _ in factors}
    return {
        "jurisdictions": [c for c in parsed.get("jurisdictions", []) if c in jur_codes],
        "factors":       [c for c in parsed.get("factors", []) if c in fac_codes],
        "intent":        str(parsed.get("intent", "")).strip(),
    }
