"""Parse free-form statute citations.

Handles:
    "CA Veh Code 22107"
    "Cal. Veh. Code § 22350"
    "Cal. Veh. Code § 2800.1(a)"
    "California Vehicle Code §22107"
    "CA §23152"
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
    "veh":            "Vehicle Code",
    "vehicle":        "Vehicle Code",
    "vehicle code":   "Vehicle Code",
    "vc":             "Vehicle Code",
    "veh code":       "Vehicle Code",
    "vehicle and traffic": "Vehicle and Traffic Law",
    "transportation": "Transportation Code",
}

# Section numbers in the eval CSV look like "2800.1(a)" or "21453(a)-(b)".
# Allow dots, hyphens, parens, letters as part of the section token.
_SECTION_TOKEN = r"\d[\w\.\-\(\)]*"

_PATTERN = re.compile(
    rf"""
    (?P<jur>[A-Za-z\.]+)\s*\.?\s*           # CA / Cal. / California
    (?:(?P<code>[A-Za-z\.\s]+?)\s*Code\s*)? # optional "Veh / Vehicle / VC Code"
    §?\s*
    (?P<section>{_SECTION_TOKEN})
    """,
    re.VERBOSE,
)

# Bare-jurisdiction form: "CA §22107" or "CA 22107"
_BARE_JUR = re.compile(rf"^\s*(?P<jur>[A-Za-z]+)\s*§?\s*(?P<section>{_SECTION_TOKEN})\s*$")


@dataclass
class Citation:
    jurisdiction: str
    code_name: str | None
    section: str


def parse(text: str) -> Citation | None:
    text = text.strip()
    if not text:
        return None

    # Bare form like "CA 22107" — no code mentioned.
    bm = _BARE_JUR.match(text)
    if bm:
        jur = JURISDICTION_ALIASES.get(bm.group("jur").lower().rstrip("."))
        if jur:
            return Citation(jurisdiction=jur, code_name=None, section=bm.group("section"))

    m = _PATTERN.search(text)
    if not m:
        return None

    jur_raw = m.group("jur").lower().rstrip(".")
    jurisdiction = JURISDICTION_ALIASES.get(jur_raw)
    if not jurisdiction:
        return None

    code_raw = (m.group("code") or "").lower().strip().rstrip(".")
    code_name = CODE_ALIASES.get(code_raw) if code_raw else None

    return Citation(jurisdiction=jurisdiction, code_name=code_name, section=m.group("section"))
