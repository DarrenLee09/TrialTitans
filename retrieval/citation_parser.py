"""Parse free-form statute citations.

Layered match — most specific to least:

    1. <jurisdiction> <code> §<section>(<subsection>)?   "Cal. Veh. Code §2800.1(a)"
    2. <jurisdiction> <section>                          "CA 23152"      → CA Vehicle Code
    3. <code> Code §<section>(<subsection>)?             "Veh. Code §23152" → CA + ...
    4. §?<section>(<subsection>)?                        "§23152" / "23152" → CA Vehicle Code

Defaults: missing jurisdiction → CA, missing code → Vehicle Code.
The bare-section path uses fullmatch so "23152 cases" does NOT parse — that
falls through to FTS/vector search, where it belongs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

JURISDICTION_ALIASES = {
    "ca":  "CA", "cal": "CA", "calif": "CA", "california": "CA",
    "ny":  "NY", "new york": "NY",
    "tx":  "TX", "texas": "TX",
    "fl":  "FL", "florida": "FL",
    "il":  "IL", "illinois": "IL",
    "ga":  "GA", "georgia": "GA",
    "oh":  "OH", "ohio": "OH",
}

CODE_ALIASES = {
    "veh":     "Vehicle Code",
    "vehicle": "Vehicle Code",
    "vc":      "Vehicle Code",
}

DEFAULT_JURISDICTION = "CA"
DEFAULT_CODE = "Vehicle Code"


@dataclass
class Citation:
    jurisdiction: str
    code_name: str
    section: str
    subsection: str | None = None


# Section: digits, optional .decimal, optional -segments, optional letter suffix.
# Examples: 23152, 2800.1, 11-501, 40-6-181, 23152a
_SECTION = r"\d+(?:\.\d+)?(?:-\d+)*[a-zA-Z]?"
# Subsection marker: "(a)" or "(a)-(b)"
_SUBSEC = r"\([a-zA-Z](?:\)-\([a-zA-Z]\))?\)"
_SECTION_AND_SUB = rf"(?P<section>{_SECTION})(?P<subsection>{_SUBSEC})?"

_FULL_RE = re.compile(
    rf"^\s*(?P<jur>[A-Za-z]+)\.?\s+(?P<code>[A-Za-z]+)\.?(?:\s+Code)?\s*§?\s*{_SECTION_AND_SUB}\s*$",
    re.IGNORECASE,
)

_JUR_SECTION_RE = re.compile(
    rf"^\s*(?P<jur>[A-Za-z]+)\.?\s+§?\s*{_SECTION_AND_SUB}\s*$",
    re.IGNORECASE,
)

_CODE_SECTION_RE = re.compile(
    rf"^\s*(?P<code>[A-Za-z]+)\.?\s*Code\s*§?\s*{_SECTION_AND_SUB}\s*$",
    re.IGNORECASE,
)

_BARE_SECTION_RE = re.compile(rf"^\s*§?\s*{_SECTION_AND_SUB}\s*$")


def _norm(s: str) -> str:
    return s.lower().strip().rstrip(".")


def parse(text: str) -> Citation | None:
    text = text.strip()
    if not text:
        return None

    m = _FULL_RE.match(text)
    if m:
        jur = JURISDICTION_ALIASES.get(_norm(m.group("jur")))
        code = CODE_ALIASES.get(_norm(m.group("code")))
        if jur and code:
            return Citation(jur, code, m.group("section"), m.group("subsection"))

    m = _JUR_SECTION_RE.match(text)
    if m:
        jur = JURISDICTION_ALIASES.get(_norm(m.group("jur")))
        if jur:
            return Citation(jur, DEFAULT_CODE, m.group("section"), m.group("subsection"))

    m = _CODE_SECTION_RE.match(text)
    if m:
        code = CODE_ALIASES.get(_norm(m.group("code")))
        if code:
            return Citation(DEFAULT_JURISDICTION, code, m.group("section"), m.group("subsection"))

    m = _BARE_SECTION_RE.fullmatch(text)
    if m:
        return Citation(
            DEFAULT_JURISDICTION,
            DEFAULT_CODE,
            m.group("section"),
            m.group("subsection"),
        )

    return None
