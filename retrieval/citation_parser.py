"""Parse free-form statute citations like "CA Veh Code 22107" or "Cal. Vehicle Code § 22350"."""
from __future__ import annotations

import re
from dataclasses import dataclass

JURISDICTION_ALIASES = {
    "ca":  "CA", "cal": "CA", "calif": "CA", "california": "CA",
    "ny":  "NY", "new york": "NY",
    "tx":  "TX", "texas": "TX",
    "fl":  "FL", "florida": "FL",
}

CODE_ALIASES = {
    "veh":     "Vehicle Code",
    "vehicle": "Vehicle Code",
    "vc":      "Vehicle Code",
}


@dataclass
class Citation:
    jurisdiction: str
    code_name: str
    section: str


_PATTERN = re.compile(
    r"""
    (?P<jur>[A-Za-z\.]+)\s*           # CA / Cal. / California
    (?P<code>[A-Za-z\.\s]+?)          # Veh / Vehicle / VC
    \s*(?:Code)?\s*§?\s*
    (?P<section>\d+(?:\.\d+)?[a-zA-Z]?)
    """,
    re.VERBOSE,
)


def parse(text: str) -> Citation | None:
    m = _PATTERN.search(text)
    if not m:
        return None

    jur_raw = m.group("jur").lower().rstrip(".")
    code_raw = m.group("code").lower().strip().rstrip(".")

    jurisdiction = JURISDICTION_ALIASES.get(jur_raw)
    code_name = CODE_ALIASES.get(code_raw)

    if not jurisdiction or not code_name:
        return None

    return Citation(jurisdiction=jurisdiction, code_name=code_name, section=m.group("section"))
