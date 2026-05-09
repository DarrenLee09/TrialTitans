"""Scrape state statute sections from FindLaw's public codes sitemap.

FindLaw mirrors many state codes (NY, FL, etc.) at codes.findlaw.com. Each
section is a static page with the citation in the H1 and the body in a
`.codes-content` div, and every URL is listed in a sitemap — so we walk the
sitemap rather than crawling navigation.

URL pattern observed:
    https://codes.findlaw.com/<state>/<law-slug>/<prefix>-sect-<section>/

Example:
    https://codes.findlaw.com/ny/vehicle-and-traffic-law/vat-sect-1192/
        prefix="vat", section="1192"
"""
from __future__ import annotations

import argparse
import re
import time
from dataclasses import dataclass
from typing import Iterable

import httpx
from bs4 import BeautifulSoup

from db.seed import connect

SITEMAP_INDEX = "https://codes.findlaw.com/sitemapindex.xml"
REQUEST_DELAY_S = 0.35
REQUEST_TIMEOUT_S = 25.0
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Map FindLaw URL slugs to canonical citation prefixes used by attorneys.
# Slug → (jurisdiction_code, citation_prefix). Extend as needed.
LAW_SLUGS: dict[str, tuple[str, str]] = {
    # New York
    "ny/vehicle-and-traffic-law":          ("NY", "VAT"),
    "ny/penal-law":                        ("NY", "Penal Law"),
    "ny/criminal-procedure-law":           ("NY", "CPL"),
    "ny/civil-practice-law-and-rules":     ("NY", "CPLR"),
    "ny/general-business-law":             ("NY", "GBL"),
    "ny/general-obligations-law":          ("NY", "GOL"),
    "ny/insurance-law":                    ("NY", "Ins Law"),
    "ny/labor-law":                        ("NY", "Labor Law"),
    "ny/public-health-law":                ("NY", "PHL"),
    "ny/tax-law":                          ("NY", "Tax Law"),
    # Florida — FindLaw groups FL by Title (e.g. title-xxiii-motor-vehicles).
    # The citation prefix in FL is just "Fla. Stat." with section like "316.193".
    "fl/title-xxiii-motor-vehicles":       ("FL", "Fla. Stat."),
    "fl/title-xlvi-crimes":                ("FL", "Fla. Stat."),
    "fl/title-xli-statutes-of-limitations-criminal-actions": ("FL", "Fla. Stat."),
    "fl/title-vi-civil-practice-and-procedure":              ("FL", "Fla. Stat."),
    "fl/title-xlv-torts":                  ("FL", "Fla. Stat."),
    "fl/title-xx-public-health":           ("FL", "Fla. Stat."),
    "fl/title-xxxiii-regulation-of-trade-commerce-investments-and-solicitations": ("FL", "Fla. Stat."),
}

_SECTION_FROM_SLUG = re.compile(r"-sect-([\w\d\-\.]+?)/?$")
_H1_CITE = re.compile(r"§\s*([\w\d\.\-]+)\.?\s*(.*?)$", re.DOTALL)


@dataclass(slots=True)
class FindLawRecord:
    section_number: str
    title: str | None
    full_text: str
    source_url: str


class FindLawClient:
    def __init__(self, delay_s: float = REQUEST_DELAY_S) -> None:
        self.delay_s = delay_s
        self.client = httpx.Client(
            follow_redirects=True,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT_S,
        )
        self._last = 0.0

    def __enter__(self) -> "FindLawClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.client.close()

    def get(self, url: str) -> str:
        elapsed = time.monotonic() - self._last
        if elapsed < self.delay_s:
            time.sleep(self.delay_s - elapsed)
        r = self.client.get(url)
        self._last = time.monotonic()
        r.raise_for_status()
        return r.text


def list_state_sitemaps(state: str, client: FindLawClient) -> list[str]:
    body = client.get(SITEMAP_INDEX)
    needle = f"/{state.lower()}/"
    return re.findall(rf"<loc>(https://codes\.findlaw\.com/sitemapcodes/v\d+/{state.lower()}/sitemap\d+\.xml)</loc>", body)


def list_section_urls(sitemap_url: str, client: FindLawClient) -> list[str]:
    body = client.get(sitemap_url)
    return re.findall(r"<loc>(https://codes\.findlaw\.com/[^<]+)</loc>", body)


def filter_urls_for_law(urls: Iterable[str], law_slug: str) -> list[str]:
    needle = f"/{law_slug}/"
    return [u for u in urls if needle in u and "-sect-" in u]


def parse_section_page(html: str, source_url: str) -> FindLawRecord | None:
    soup = BeautifulSoup(html, "html.parser")

    # Section number is reliably in the URL slug.
    slug_match = _SECTION_FROM_SLUG.search(source_url)
    if not slug_match:
        return None
    section_number = slug_match.group(1).upper()

    # Title: H1 typically reads "<state law name> - <prefix> § <section>. <Title>"
    title: str | None = None
    h1 = soup.find("h1")
    if h1:
        h1_text = h1.get_text(" ", strip=True)
        m = re.search(r"§\s*[\w\d\.\-]+\.?\s*(.+)$", h1_text)
        if m:
            title = m.group(1).strip().rstrip(".")
            if len(title) > 200:
                title = title[:200].rstrip() + "…"

    # Body: .codes-content
    body_node = soup.select_one(".codes-content")
    if body_node is None:
        # Some pages put it in main / article. Fall back.
        body_node = soup.select_one("main") or soup.select_one("article")
    if body_node is None:
        return None

    # Strip nav / aside / script / style children.
    for noise in body_node.select("script, style, nav, aside, .ads, .ad-container"):
        noise.decompose()

    body_text = body_node.get_text("\n", strip=True)
    body_text = re.sub(r"\n{3,}", "\n\n", body_text)
    if len(body_text) < 40:
        return None

    return FindLawRecord(
        section_number=section_number,
        title=title,
        full_text=body_text,
        source_url=source_url,
    )


def _get_jurisdiction_id(jurisdiction_code: str) -> int:
    with connect() as conn:
        row = conn.execute(
            "SELECT id FROM jurisdictions WHERE code = ?", (jurisdiction_code,)
        ).fetchone()
        if not row:
            raise RuntimeError(
                f"{jurisdiction_code} jurisdiction not found; run `python -m db.seed` first."
            )
        return int(row["id"])


def _normalize_section(jurisdiction: str, section: str) -> str:
    # FindLaw URL slugs use "-" for the dot in real FL section numbers
    # (e.g. URL "316-001" → real citation "§316.001"). NY uses dashes literally
    # for sub-sections like §404-OO, so leave NY untouched.
    if jurisdiction == "FL":
        return section.replace("-", ".")
    return section


def _citation_for(jurisdiction: str, prefix: str, section: str) -> str:
    return f"{jurisdiction} {prefix} §{_normalize_section(jurisdiction, section)}"


def _save_records(records: list[FindLawRecord], jurisdiction_id: int, jurisdiction: str, prefix: str) -> int:
    if not records:
        return 0
    with connect() as conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO statutes(
                jurisdiction_id,
                citation,
                section_number,
                title,
                full_text,
                source_url,
                is_verified
            ) VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            [
                (
                    jurisdiction_id,
                    _citation_for(jurisdiction, prefix, r.section_number),
                    _normalize_section(jurisdiction, r.section_number),
                    r.title,
                    r.full_text,
                    r.source_url,
                )
                for r in records
            ],
        )
        conn.commit()
    return len(records)


def scrape_law(law_slug: str, limit: int = 0) -> int:
    if law_slug not in LAW_SLUGS:
        raise SystemExit(
            f"Unknown law slug: {law_slug!r}. Known: {sorted(LAW_SLUGS)}"
        )
    jurisdiction, prefix = LAW_SLUGS[law_slug]
    state = law_slug.split("/", 1)[0]
    jurisdiction_id = _get_jurisdiction_id(jurisdiction)

    with FindLawClient() as client:
        sitemaps = list_state_sitemaps(state, client)
        print(f"[{law_slug}] discovered {len(sitemaps)} sitemap(s)", flush=True)
        all_urls: list[str] = []
        for sm in sitemaps:
            urls = list_section_urls(sm, client)
            all_urls.extend(urls)
        section_urls = filter_urls_for_law(all_urls, law_slug)
        print(f"[{law_slug}] section URLs: {len(section_urls)}", flush=True)
        if limit > 0:
            section_urls = section_urls[:limit]

        stored = 0
        batch: list[FindLawRecord] = []
        for i, url in enumerate(section_urls, start=1):
            try:
                html = client.get(url)
            except httpx.HTTPError as exc:
                print(f"  [warn] {url}: {exc}", flush=True)
                continue
            try:
                rec = parse_section_page(html, url)
            except Exception as exc:
                print(f"  [warn] parse failed {url}: {exc}", flush=True)
                continue
            if rec is None:
                continue
            batch.append(rec)
            if len(batch) >= 50:
                stored += _save_records(batch, jurisdiction_id, jurisdiction, prefix)
                batch = []
                print(f"  [{i}/{len(section_urls)}] stored so far: {stored}", flush=True)
        if batch:
            stored += _save_records(batch, jurisdiction_id, jurisdiction, prefix)
        print(f"[{law_slug}] Stored {stored} section(s)", flush=True)
        return stored


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--law",
        required=True,
        help=f"Law slug to scrape. Known: {sorted(LAW_SLUGS)} or 'all-ny' / 'all-fl' for every registered law in that state.",
    )
    parser.add_argument("--limit", type=int, default=0, help="Max sections per law (0 = all)")
    args = parser.parse_args()

    if args.law in {"all-ny", "all-fl"}:
        state = args.law.split("-", 1)[1]
        slugs = [s for s in LAW_SLUGS if s.startswith(f"{state}/")]
    else:
        slugs = [args.law]

    total = 0
    for slug in slugs:
        total += scrape_law(slug, limit=args.limit)
    print(f"TOTAL stored across {len(slugs)} law(s): {total}", flush=True)


if __name__ == "__main__":
    main()
