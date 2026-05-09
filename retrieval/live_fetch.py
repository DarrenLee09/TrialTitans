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


def _extract_h1_title(soup) -> Optional[str]:
    """Pull the human-readable title out of a FindLaw section H1. Splits on
    the section-number reference and keeps what follows. Requires the title
    to start with a letter so '§ 40-5-55' (no caption) doesn't yield title='5'
    via greedy regex backtracking."""
    h1 = soup.find("h1")
    if not h1:
        return None
    text = h1.get_text(" ", strip=True)
    parts = re.split(r"§\s*[\w\d\.\-]+", text, maxsplit=1)
    if len(parts) < 2:
        return None
    candidate = parts[1].strip().lstrip(".—-:·").strip()
    if not candidate or not candidate[0].isalpha():
        return None
    if len(candidate) > 200:
        candidate = candidate[:200].rstrip() + "…"
    return candidate


def _clean_findlaw_body(text: str) -> str:
    """Strip leading FindLaw breadcrumb / heading lines that sometimes land
    inside .codes-content above the actual statute prose."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    breadcrumb_markers = (
        "FindLaw", "Georgia Code", "New York Consolidated Laws",
        "Ohio Revised Code", "Code Title", "Title", "Cases", "Codes", "Search",
        "Welcome to FindLaw", "Latest Blog", "For Legal Professionals",
        "Learn About The Law", "Need to Find an Attorney",
    )
    out: list[str] = []
    in_body = False
    for line in lines:
        s = line.strip()
        if not in_body:
            if s.startswith("(") or (len(s) >= 40 and not any(s.startswith(m) for m in breadcrumb_markers)):
                in_body = True
                out.append(line)
            continue
        out.append(line)
    cleaned = "\n".join(out) if out else text
    return re.sub(r"\n{3,}", "\n\n", cleaned)
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

# GA and OH FindLaw coverage uses a different URL shape — title-prefixed
# slugs with "ga-code-sect" / "oh-rev-code-sect" markers. Fetcher just needs
# the title slug; the section number is appended dash-delimited.
GA_TITLE_SLUG = "ga/title-40-motor-vehicles-and-traffic"
OH_TITLE_SLUG = "oh/title-xlv-motor-vehicles-aeronautics-watercraft"


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
    text = _clean_findlaw_body(text)
    if len(text) < 60:
        return None
    title = _extract_h1_title(soup)
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


def _fetch_findlaw_simple(state_label: str, jurisdiction_code: str,
                          title_slug: str, sect_marker: str,
                          code_name: str, section: str) -> Optional[dict]:
    """Generic FindLaw fetcher for states whose URL is `<title-slug>/<marker>-<section>/`."""
    sec_slug = section.lower().replace(".", "-")
    url = f"https://codes.findlaw.com/{title_slug}/{sect_marker}-{sec_slug}/"
    try:
        r = httpx.get(url, headers=HEADERS, timeout=TIMEOUT_S, follow_redirects=True)
    except httpx.HTTPError:
        return None
    if r.status_code != 200 or "404 Error" in r.text[:5000]:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    body_node = soup.select_one(".codes-content")
    if body_node is None:
        return None
    for noise in body_node.select("script, style, nav, aside, .ads"):
        noise.decompose()
    text = body_node.get_text("\n", strip=True)
    text = _clean_findlaw_body(text)
    if len(text) < 60:
        return None
    title = _extract_h1_title(soup)
    record = _result_dict(jurisdiction_code, code_name, section, text, str(r.url), title)
    _save_to_db(record)
    return record


def _fetch_ga(code_name: str, section: str) -> Optional[dict]:
    return _fetch_findlaw_simple(
        "Georgia", "GA", GA_TITLE_SLUG, "ga-code-sect", code_name, section,
    )


def _fetch_oh(code_name: str, section: str) -> Optional[dict]:
    return _fetch_findlaw_simple(
        "Ohio", "OH", OH_TITLE_SLUG, "oh-rev-code-sect", code_name, section,
    )


def fetch(jurisdiction: str, code_name: str, section: str) -> Optional[dict]:
    """Try every supported source. Return a result row or None on miss."""
    if jurisdiction == "CA":
        return _fetch_ca(code_name, section)
    if jurisdiction == "NY":
        return _fetch_ny(code_name, section)
    if jurisdiction == "FL":
        return _fetch_fl(section)
    if jurisdiction == "GA":
        return _fetch_ga(code_name, section)
    if jurisdiction == "OH":
        return _fetch_oh(code_name, section)
    return None


# State → default code_name when Claude returns bare section identifiers.
_DEFAULT_CODE_NAME = {
    "GA": "Code Ann.",
    "OH": "Rev. Code",
    "FL": "Fla. Stat.",
    "CA": "Veh Code",
    "NY": "VAT",
}


def suggest_and_fetch(query: str, jurisdiction: str, limit: int = 5) -> list[dict]:
    """Agent-style retrieval for jurisdictions with no pre-scraped index.

    Asks Claude for the most likely statute sections matching the user's
    natural-language query in the given state, then live-fetches each
    candidate from its canonical source. Returns whatever fetched.
    """
    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return []
    try:
        from anthropic import Anthropic
    except ImportError:
        return []

    code_label = {
        "GA": "Georgia Code (e.g. 40-6-391)",
        "OH": "Ohio Revised Code (e.g. 4511.19)",
        "FL": "Florida Statutes (e.g. 316.193)",
        "CA": "California Vehicle/Penal Code (e.g. 22107, 23152)",
        "NY": "New York Vehicle and Traffic Law / Penal Law (e.g. 1192)",
    }.get(jurisdiction, "the state code")

    client = Anthropic()
    prompt = (
        f"A personal-injury attorney asked: {query!r}\n\n"
        f"Suggest up to {limit} specific {code_label} sections most likely on point. "
        "Reply with ONLY a JSON list of bare section identifiers as strings, "
        'e.g. ["40-6-391", "40-6-181"]. No prose.'
    )
    try:
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text if msg.content else ""
    except Exception:
        return []

    import json
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\s*|\s*```$", "", text)
    try:
        sections = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return []
    if not isinstance(sections, list):
        return []

    code_name = _DEFAULT_CODE_NAME.get(jurisdiction, jurisdiction)
    # Dedupe + cap; preserve Claude's suggested order so RRF favours the
    # top-ranked sections.
    seen: set[str] = set()
    candidates: list[str] = []
    for sec in sections[:limit]:
        if not isinstance(sec, str):
            continue
        sec = sec.strip()
        if not sec or sec in seen:
            continue
        seen.add(sec)
        candidates.append(sec)

    # Fetch in parallel — each section is one independent HTTP round trip
    # to the canonical source. Sequential was ~1s × N; threaded brings the
    # entire batch down to ~one fetch's worth of latency.
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=min(8, max(2, len(candidates)))) as pool:
        records = list(pool.map(lambda s: fetch(jurisdiction, code_name, s), candidates))
    return [r for r in records if r]
