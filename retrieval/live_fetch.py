"""Fetch a statute live from its canonical source on a citation-lookup miss.

Used by query_router as a fallback when a parsed citation isn't in the local
DB. Hits the official site, parses the section page, caches the result back
into the DB, and returns it as a normal result row. Failures return None — the
caller falls through to FTS.

Supported sources:
- CA: leginfo.legislature.ca.gov (section-specific URL, fast)
- NY: codes.findlaw.com (mirror; static HTML; was already working in scraper)
- FL: flsenate.gov (official; section-specific URL; cleaner than FindLaw)
"""
from __future__ import annotations

import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from db.seed import connect

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT_S = 10.0


# code_name → CA leginfo lawCode token
CA_NAME_TO_TOKEN: dict[str, str] = {
    "Veh Code": "VEH",
    "Pen Code": "PEN",
    "Civ Code": "CIV",
    "Code Civ Proc": "CCP",
    "Bus & Prof Code": "BPC",
    "Com Code": "COM",
    "Corp Code": "CORP",
    "Educ Code": "EDC",
    "Elec Code": "ELEC",
    "Evid Code": "EVID",
    "Fam Code": "FAM",
    "Fin Code": "FIN",
    "Food & Agric Code": "FAC",
    "Gov Code": "GOV",
    "Harb & Nav Code": "HNC",
    "Health & Safety Code": "HSC",
    "Ins Code": "INS",
    "Lab Code": "LAB",
    "Mil & Vet Code": "MVC",
    "Prob Code": "PROB",
    "Pub Cont Code": "PCC",
    "Pub Resources Code": "PRC",
    "Pub Util Code": "PUC",
    "Rev & Tax Code": "RTC",
    "Sts & Hwys Code": "SHC",
    "Unemp Ins Code": "UIC",
    "Wat Code": "WAT",
    "Welf & Inst Code": "WIC",
}

# code_name → (FindLaw law slug, citation prefix in URL)
NY_NAME_TO_FINDLAW: dict[str, tuple[str, str]] = {
    "VAT": ("ny/vehicle-and-traffic-law", "vat"),
    "Penal Law": ("ny/penal-law", "pen"),
    "CPL": ("ny/criminal-procedure-law", "cpl"),
    "CPLR": ("ny/civil-practice-law-and-rules", "cvp"),
    "GBL": ("ny/general-business-law", "gbs"),
    "GOL": ("ny/general-obligations-law", "gob"),
    "Ins Law": ("ny/insurance-law", "isc"),
    "Labor Law": ("ny/labor-law", "lab"),
    "PHL": ("ny/public-health-law", "pbh"),
    "Tax Law": ("ny/tax-law", "tax"),
}


def _save_to_db(record: dict) -> None:
    """Cache a live-fetched record so future queries skip the network hop."""
    with connect() as conn:
        jur_row = conn.execute(
            "SELECT id FROM jurisdictions WHERE code = ?", (record["jurisdiction"],)
        ).fetchone()
        if not jur_row:
            return
        conn.execute(
            """
            INSERT OR REPLACE INTO statutes(
                jurisdiction_id, citation, section_number, title, full_text,
                source_url, is_verified
            ) VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            (
                int(jur_row["id"]),
                record["citation"],
                record["section"],
                record.get("title"),
                record["body"],
                record["source_url"],
            ),
        )
        conn.commit()


def _result_dict(jurisdiction: str, code_name: str, section: str, body: str,
                 source_url: str, title: Optional[str]) -> dict:
    return {
        "id": None,  # not yet in DB (caller may save)
        "jurisdiction": jurisdiction,
        "code_name": code_name,
        "section": section,
        "title": title,
        "citation": f"{jurisdiction} {code_name} §{section}",
        "body": body,
        "source_url": source_url,
        "is_live_fetch": True,
    }


def _fetch_ca(code_name: str, section: str) -> Optional[dict]:
    token = CA_NAME_TO_TOKEN.get(code_name)
    if not token:
        return None
    # leginfo expects the trailing dot for section args.
    section_arg = section if section.endswith(".") else f"{section}."
    url = (
        "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml"
        f"?lawCode={token}&sectionNum={section_arg}"
    )
    try:
        r = httpx.get(url, headers=HEADERS, timeout=TIMEOUT_S, follow_redirects=True)
    except httpx.HTTPError:
        return None
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    body_node = soup.select_one("#codeLawSectionNoHead, #manylawsections, #codeSection")
    if body_node is None:
        return None
    for noise in body_node.select("script, style, nav, .ads, .commandBar"):
        noise.decompose()
    text = body_node.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    if len(text) < 60 or "could not be loaded" in text.lower():
        return None
    record = _result_dict("CA", code_name, section, text, str(r.url), None)
    _save_to_db(record)
    return record


def _fetch_ny(code_name: str, section: str) -> Optional[dict]:
    info = NY_NAME_TO_FINDLAW.get(code_name)
    if not info:
        return None
    law_slug, prefix = info
    sec_slug = section.lower().replace(".", "-")
    url = f"https://codes.findlaw.com/{law_slug}/{prefix}-sect-{sec_slug}/"
    try:
        r = httpx.get(url, headers=HEADERS, timeout=TIMEOUT_S, follow_redirects=True)
    except httpx.HTTPError:
        return None
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    body_node = soup.select_one(".codes-content")
    if body_node is None:
        return None
    for noise in body_node.select("script, style, nav, aside, .ads, .ad-container"):
        noise.decompose()
    text = body_node.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    if len(text) < 60:
        return None
    title: Optional[str] = None
    h1 = soup.find("h1")
    if h1:
        m = re.search(r"§\s*[\w\d\.\-]+\.?\s*(.+)$", h1.get_text(" ", strip=True))
        if m:
            title = m.group(1).strip().rstrip(".")
            if len(title) > 200:
                title = title[:200].rstrip() + "…"
    record = _result_dict("NY", code_name, section, text, str(r.url), title)
    _save_to_db(record)
    return record


def _fetch_fl(section: str) -> Optional[dict]:
    url = f"https://www.flsenate.gov/Laws/Statutes/2024/{section}"
    try:
        r = httpx.get(url, headers=HEADERS, timeout=TIMEOUT_S, follow_redirects=True)
    except httpx.HTTPError:
        return None
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    body_node = soup.select_one(".SectionBody, .Section, #statute")
    if body_node is None:
        body_node = soup.select_one("main")
    if body_node is None:
        return None
    for noise in body_node.select("script, style, nav, aside, .ads"):
        noise.decompose()
    text = body_node.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    if len(text) < 60:
        return None
    record = _result_dict("FL", "Fla. Stat.", section, text, str(r.url), None)
    _save_to_db(record)
    return record


def fetch(jurisdiction: str, code_name: str, section: str) -> Optional[dict]:
    """Try every supported source. Return a result row or None on miss."""
    if jurisdiction == "CA":
        return _fetch_ca(code_name, section)
    if jurisdiction == "NY":
        return _fetch_ny(code_name, section)
    if jurisdiction == "FL":
        return _fetch_fl(section)
    return None
