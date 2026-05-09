"""Parse free-form statute citations like "CA Veh Code 22107" or "Cal. Penal Code § 187"."""
from __future__ import annotations

import re
from dataclasses import dataclass

JURISDICTION_ALIASES = {
    "ca":  "CA", "cal": "CA", "calif": "CA", "california": "CA",
    "ny":  "NY", "n y": "NY", "new york": "NY",
    "fl":  "FL", "fla": "FL", "florida": "FL",
    "ga":  "GA", "georgia": "GA",
    "oh":  "OH", "ohio": "OH",
}

# Maps a normalized lowercase code phrase → canonical short code name.
# All CA codes that the leginfo scraper supports are listed.
CODE_ALIASES = {
    # Vehicle
    "veh": "Veh Code", "vehicle": "Veh Code", "vc": "Veh Code",
    # Penal
    "pen": "Pen Code", "penal": "Pen Code", "pc": "Pen Code",
    # Civil
    "civ": "Civ Code", "civil": "Civ Code", "cc": "Civ Code",
    # Code of Civil Procedure
    "ccp": "Code Civ Proc", "code civ proc": "Code Civ Proc",
    "code of civil procedure": "Code Civ Proc",
    # Business & Professions
    "bpc": "Bus & Prof Code", "bus & prof": "Bus & Prof Code",
    "business and professions": "Bus & Prof Code",
    "business & professions": "Bus & Prof Code",
    # Health & Safety
    "hsc": "Health & Safety Code", "health & safety": "Health & Safety Code",
    "health and safety": "Health & Safety Code",
    # Government
    "gov": "Gov Code", "government": "Gov Code",
    # Labor
    "lab": "Lab Code", "labor": "Lab Code",
    # Welfare & Institutions
    "wic": "Welf & Inst Code", "welf & inst": "Welf & Inst Code",
    "welfare and institutions": "Welf & Inst Code",
    # Evidence
    "evid": "Evid Code", "evidence": "Evid Code",
    # Insurance
    "ins": "Ins Code", "insurance": "Ins Code",
    # Probate
    "prob": "Prob Code", "probate": "Prob Code",
    # Family
    "fam": "Fam Code", "family": "Fam Code",
    # Education
    "edc": "Educ Code", "educ": "Educ Code", "education": "Educ Code",
    # Corporations
    "corp": "Corp Code", "corporations": "Corp Code",
    # Revenue & Tax
    "rtc": "Rev & Tax Code", "revenue and taxation": "Rev & Tax Code",
    # Public Utilities
    "puc": "Pub Util Code", "public utilities": "Pub Util Code",
    # Public Resources
    "prc": "Pub Resources Code", "public resources": "Pub Resources Code",
    # Public Contract
    "pcc": "Pub Cont Code", "public contract": "Pub Cont Code",
    # Streets & Highways
    "shc": "Sts & Hwys Code", "streets & highways": "Sts & Hwys Code",
    "streets and highways": "Sts & Hwys Code",
    # Water
    "wat": "Wat Code", "water": "Wat Code",
    # Commercial
    "com": "Com Code", "commercial": "Com Code",
    # Financial
    "fin": "Fin Code", "financial": "Fin Code",
    # Food & Agricultural
    "fac": "Food & Agric Code", "food and agricultural": "Food & Agric Code",
    # Harbors & Navigation
    "hnc": "Harb & Nav Code", "harbors and navigation": "Harb & Nav Code",
    # Military & Veterans
    "mvc": "Mil & Vet Code", "military and veterans": "Mil & Vet Code",
    # Unemployment Insurance
    "uic": "Unemp Ins Code", "unemployment insurance": "Unemp Ins Code",
    # Elections
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

    # ---------- Florida ----------
    # FL section numbers carry the chapter inline (e.g. 316.193), so the
    # citation prefix is universal: "Fla. Stat." — no per-title differentiation.
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


@dataclass
class Citation:
    jurisdiction: str
    code_name: str
    section: str


_PATTERN = re.compile(
    r"""
    (?P<jur>[A-Za-z\.]+)\s*
    (?P<code>(?:[A-Za-z\.&]+\s*)+?)
    \s*(?:Code|Law|Statutes?|Stat\.?)?\s*§?\s*
    (?P<section>\d+(?:[\.\-][\w]+)*[a-zA-Z]?)
    """,
    re.VERBOSE,
)


def parse(text: str) -> Citation | None:
    m = _PATTERN.search(text)
    if not m:
        return None

    jur_raw = m.group("jur").lower().rstrip(".")
    code_raw = m.group("code").lower().strip().rstrip(".")
    code_raw = re.sub(r"\s+", " ", code_raw)

    jurisdiction = JURISDICTION_ALIASES.get(jur_raw)
    code_name = CODE_ALIASES.get(code_raw)

    if not jurisdiction or not code_name:
        return None

    return Citation(jurisdiction=jurisdiction, code_name=code_name, section=m.group("section"))
