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
    "ny":  "NY", "n y": "NY", "new york": "NY",
    "fl":  "FL", "fla": "FL", "florida": "FL",
    "ga":  "GA", "georgia": "GA",
    "oh":  "OH", "ohio": "OH",
    # Parsed but not in the jurisdictions dropdown — judges may still cite them.
    "tx":  "TX", "texas": "TX",
    "il":  "IL", "illinois": "IL",
}

# Maps a normalized lowercase code phrase → canonical short code name.
# Covers CA's 28 codes plus NY laws, FL, GA, OH conventions.
CODE_ALIASES = {
    # ---------- California (28 codes from leginfo.legislature.ca.gov) ----------
    "veh": "Vehicle Code", "vehicle": "Vehicle Code", "vc": "Vehicle Code",
    "pen": "Pen Code", "penal": "Pen Code", "pc": "Pen Code",
    "civ": "Civ Code", "civil": "Civ Code", "cc": "Civ Code",
    "ccp": "Code Civ Proc", "code civ proc": "Code Civ Proc",
    "code of civil procedure": "Code Civ Proc",
    "bpc": "Bus & Prof Code", "bus & prof": "Bus & Prof Code",
    "business and professions": "Bus & Prof Code",
    "business & professions": "Bus & Prof Code",
    "hsc": "Health & Safety Code", "health & safety": "Health & Safety Code",
    "health and safety": "Health & Safety Code",
    "gov": "Gov Code", "government": "Gov Code",
    "lab": "Lab Code", "labor": "Lab Code",
    "wic": "Welf & Inst Code", "welf & inst": "Welf & Inst Code",
    "welfare and institutions": "Welf & Inst Code",
    "evid": "Evid Code", "evidence": "Evid Code",
    "ins": "Ins Code", "insurance": "Ins Code",
    "prob": "Prob Code", "probate": "Prob Code",
    "fam": "Fam Code", "family": "Fam Code",
    "edc": "Educ Code", "educ": "Educ Code", "education": "Educ Code",
    "corp": "Corp Code", "corporations": "Corp Code",
    "rtc": "Rev & Tax Code", "revenue and taxation": "Rev & Tax Code",
    "puc": "Pub Util Code", "public utilities": "Pub Util Code",
    "prc": "Pub Resources Code", "public resources": "Pub Resources Code",
    "pcc": "Pub Cont Code", "public contract": "Pub Cont Code",
    "shc": "Sts & Hwys Code", "streets & highways": "Sts & Hwys Code",
    "streets and highways": "Sts & Hwys Code",
    "wat": "Wat Code", "water": "Wat Code",
    "com": "Com Code", "commercial": "Com Code",
    "fin": "Fin Code", "financial": "Fin Code",
    "fac": "Food & Agric Code", "food and agricultural": "Food & Agric Code",
    "hnc": "Harb & Nav Code", "harbors and navigation": "Harb & Nav Code",
    "mvc": "Mil & Vet Code", "military and veterans": "Mil & Vet Code",
    "uic": "Unemp Ins Code", "unemployment insurance": "Unemp Ins Code",
    "elec": "Elec Code", "elections": "Elec Code",

    # ---------- New York ----------
    "vat": "VAT", "vehicle and traffic": "VAT", "vehicle and traffic law": "VAT",
    "penal law": "Penal Law", "pl": "Penal Law",
    "cpl": "CPL", "criminal procedure": "CPL", "criminal procedure law": "CPL",
    "cplr": "CPLR", "civil practice law and rules": "CPLR",
    "gbl": "GBL", "general business law": "GBL",
    "gol": "GOL", "general obligations law": "GOL",
    "ins law": "Ins Law", "insurance law": "Ins Law",
    "labor law": "Labor Law",
    "phl": "PHL", "public health law": "PHL",
    "tax law": "Tax Law",

    # ---------- Florida (universal "Fla. Stat." prefix; chapter is in the section) ----------
    "stat": "Fla. Stat.", "stat.": "Fla. Stat.",
    "fla stat": "Fla. Stat.", "fla. stat.": "Fla. Stat.", "fla stat.": "Fla. Stat.",
    "florida statutes": "Fla. Stat.",

    # ---------- Georgia ----------
    "code": "Code Ann.", "code ann": "Code Ann.", "code ann.": "Code Ann.",
    "ga code": "Code Ann.", "ga code ann": "Code Ann.", "ga code ann.": "Code Ann.",

    # ---------- Ohio ----------
    "rev": "Rev. Code", "rev.": "Rev. Code",
    "rev code": "Rev. Code", "rev. code": "Rev. Code",
    "ohio rev code": "Rev. Code", "ohio rev. code": "Rev. Code",
    "revised code": "Rev. Code", "revised": "Rev. Code",
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

# Multi-word codes ("Code Civ Proc", "Bus & Prof", "Vehicle and Traffic")
# need to greedily eat up to "Code|Law|Stat|Ann|Statutes" before the section.
_FULL_RE = re.compile(
    rf"^\s*(?P<jur>[A-Za-z]+)\.?\s+(?P<code>(?:[A-Za-z\.&]+\s*)+?)\s*(?:Code|Law|Statutes?|Stat\.?|Ann\.?)?\s*§?\s*{_SECTION_AND_SUB}\s*$",
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
    return re.sub(r"\s+", " ", s.lower().strip().rstrip("."))


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

    m = _BARE_SECTION_RE.match(text)
    if m:
        return Citation(DEFAULT_JURISDICTION, DEFAULT_CODE, m.group("section"), m.group("subsection"))

    return None
