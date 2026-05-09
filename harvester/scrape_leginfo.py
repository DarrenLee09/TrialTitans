"""Scrape California Legislative Information code sections into SQLite."""
from __future__ import annotations

import argparse
import re
import time
from collections import deque
from dataclasses import dataclass
from html import unescape
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import httpx
from bs4 import BeautifulSoup

from db.seed import connect

BASE_URL = "https://leginfo.legislature.ca.gov"
DEFAULT_CODE = "VEH"
REQUEST_DELAY_S = 0.5
REQUEST_TIMEOUT_S = 30.0
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
SECTION_RE = re.compile(
    r"(?:^|\n)\s*(\d{1,6}(?:\.\d+)?)\.\s{2,}(.*?)(?=\n\s*\d{1,6}(?:\.\d+)?\.\s{2,}|\Z)",
    re.DOTALL,
)
AMENDMENT_NOTE_RE = re.compile(
    r"(\((?:Added|Amended|Enacted|Formerly|Operative|Renumbered|Repealed|Repealed and added|Section added|Section repealed).*?\))\s*$",
    re.IGNORECASE | re.DOTALL,
)
EFFECTIVE_DATE_RE = re.compile(r"Effective\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", re.IGNORECASE)
SECTION_NUMBER_RE = re.compile(r"^\d{1,6}(?:\.\d+)?\.$")


@dataclass(slots=True)
class StatuteRecord:
    section_number: str
    title: str | None
    full_text: str
    source_url: str


class LegInfoClient:
    def __init__(self, delay_s: float = REQUEST_DELAY_S) -> None:
        self.delay_s = delay_s
        self.client = httpx.Client(
            follow_redirects=True,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT_S,
        )
        self._last_request_at = 0.0

    def __enter__(self) -> "LegInfoClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.client.close()

    def get(self, url: str) -> tuple[str, str]:
        now = time.monotonic()
        elapsed = now - self._last_request_at
        if elapsed < self.delay_s:
            time.sleep(self.delay_s - elapsed)
        response = self.client.get(url)
        self._last_request_at = time.monotonic()
        response.raise_for_status()
        return response.text, str(response.url)


def _top_level_urls(code: str) -> list[str]:
    return [
        f"{BASE_URL}/faces/codes_displayexpandedbranch.xhtml?tocCode={code}&division=&title=&part=&chapter=&article=",
        f"{BASE_URL}/faces/codesTOCSelected.xhtml?tocCode={code}&tocTitle=+{code}",
    ]


def _canonicalize_url(url: str) -> str:
    parsed = urlsplit(urljoin(f"{BASE_URL}/faces/", unescape(url)))
    keep: list[tuple[str, str]] = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key in {"facelets.ui.DebugOutput", "nodetreepath"}:
            continue
        if key == "goUp" and value == "Y":
            continue
        keep.append((key, value))
    query = urlencode(sorted(keep), doseq=True)
    return urlunsplit((parsed.scheme or "https", parsed.netloc or urlsplit(BASE_URL).netloc, parsed.path, query, ""))


def _is_leginfo_path(url: str, page_name: str) -> bool:
    return urlsplit(url).path.endswith(page_name)


def _iter_leginfo_links(soup: BeautifulSoup, page_url: str, code: str) -> Iterable[str]:
    seen: set[str] = set()
    for anchor in soup.select("a[href]"):
        href = (anchor.get("href") or "").strip()
        if not href or href == "#" or href.startswith("javascript:"):
            continue
        absolute = _canonicalize_url(urljoin(page_url, href))
        if not (
            _is_leginfo_path(absolute, "codes_displayexpandedbranch.xhtml")
            or _is_leginfo_path(absolute, "codes_displayText.xhtml")
        ):
            continue
        params = dict(parse_qsl(urlsplit(absolute).query, keep_blank_values=True))
        target_code = (params.get("tocCode") or params.get("lawCode") or "").upper()
        if not target_code or target_code != code.upper():
            continue
        if absolute not in seen:
            seen.add(absolute)
            yield absolute


def _normalize_tab_text(text: str) -> str:
    normalized = text.replace("\xa0", " ")
    normalized = re.sub(r"\s*\n+\s*", "\n", normalized)
    normalized = re.sub(r"[\t\r\f\v]+", " ", normalized)
    normalized = re.sub(r" {3,}", "  ", normalized)
    return normalized.strip()


def _clean_inline_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def _extract_code_name(soup: BeautifulSoup, default_code: str) -> str:
    for heading in soup.select(".tab_content h3, .tab_content h2"):
        text = _clean_inline_text(heading.get_text(" ", strip=True))
        match = re.match(r"(.+?)\s*-\s*[A-Z0-9.]+$", text)
        if match:
            return match.group(1).strip()
    return default_code


def _extract_page_title(soup: BeautifulSoup, code: str) -> str | None:
    # Only inspect h4/h5 — these are structural DIVISION/CHAPTER/ARTICLE headings.
    # h1/h2/h3 are either chrome ("Code Text", code banner) or stray label content;
    # h6 elements are individual section-number anchors and must be excluded.
    best: str | None = None
    for heading in soup.select(".tab_content h4, .tab_content h5"):
        text = _clean_inline_text(heading.get_text(" ", strip=True))
        if not text or text == "Code Text":
            continue
        # Strip trailing section-range brackets: "[21000 - 23336]"
        text = re.sub(r"\s*\[\s*[\d.]+\s*-\s*[\d.]+\s*\]\s*$", "", text).strip()
        # Strip leading structural keyword + number: "DIVISION 11.", "CHAPTER 6.", "ARTICLE 4.5."
        text = re.sub(
            r"^(?:DIVISION|CHAPTER|ARTICLE)\s+[\d.]+\.\s*",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()
        if text:
            best = text
    return best


def _strip_amendment_note(body: str) -> tuple[str, str | None, str | None]:
    note_match = AMENDMENT_NOTE_RE.search(body)
    note_text = _clean_inline_text(note_match.group(1)) if note_match else None
    if note_match:
        body = body[: note_match.start()]
    effective_date = None
    if note_text:
        effective_match = EFFECTIVE_DATE_RE.search(note_text)
        if effective_match:
            effective_date = effective_match.group(1)
    return _clean_inline_text(body), note_text, effective_date


def _parse_sections(content: BeautifulSoup) -> list[tuple[str, str, str | None]]:
    sections: list[tuple[str, str, str | None]] = []
    seen_sections: set[str] = set()
    for block in content.select("div[align='left']"):
        if block.find("h6") is None:
            continue
        text = _normalize_tab_text(block.get_text("  ", strip=True))
        match = SECTION_RE.search(text)
        if not match:
            continue
        section = match.group(1).strip()
        body, _, effective_date = _strip_amendment_note(match.group(2))
        if not body or section in seen_sections:
            continue
        seen_sections.add(section)
        sections.append((section, body, effective_date))
    return sections


def parse_article_page(html: str, source_url: str, default_code: str) -> list[StatuteRecord]:
    soup = BeautifulSoup(html, "xml")
    content = soup.select_one(".tab_content")
    if content is None:
        return []
    sections = _parse_sections(content)
    if not sections:
        return []
    code_name = _extract_code_name(soup, default_code)
    title = _extract_page_title(soup, default_code)
    return [
        StatuteRecord(
            section_number=section,
            title=title,
            full_text=body,
            source_url=source_url,
        )
        for section, body, effective_date in sections
    ]


def get_all_article_urls(code: str) -> list[str]:
    queue: deque[str] = deque(_top_level_urls(code.upper()))
    visited: set[str] = set()
    article_urls: set[str] = set()

    with LegInfoClient() as client:
        while queue:
            next_url = _canonicalize_url(queue.popleft())
            if next_url in visited:
                continue
            visited.add(next_url)
            try:
                html, final_url = client.get(next_url)
            except httpx.HTTPError as exc:
                print(f"[warn] failed to fetch TOC page {next_url}: {exc}")
                continue

            final_url = _canonicalize_url(final_url)
            if final_url not in visited:
                visited.add(final_url)

            if _is_leginfo_path(final_url, "codes_displayText.xhtml"):
                try:
                    if parse_article_page(html, final_url, code):
                        article_urls.add(final_url)
                except Exception as exc:
                    print(f"[warn] failed to parse article page {final_url}: {exc}")

            soup = BeautifulSoup(html, "xml")
            for discovered in _iter_leginfo_links(soup, final_url, code):
                if _is_leginfo_path(discovered, "codes_displayText.xhtml"):
                    article_urls.add(discovered)
                elif discovered not in visited:
                    queue.append(discovered)

    return sorted(article_urls)


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


def _save_records(records: list[StatuteRecord], jurisdiction_id: int, jurisdiction_code: str) -> int:
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
                    f"{jurisdiction_code} Veh Code \u00a7{record.section_number}",
                    record.section_number,
                    record.title,
                    record.full_text,
                    record.source_url,
                )
                for record in records
            ],
        )
        conn.commit()
    return len(records)


def scrape_code(code: str = DEFAULT_CODE, limit: int = 0) -> int:
    jurisdiction_id = _get_jurisdiction_id("CA")
    article_urls = get_all_article_urls(code)
    if limit > 0:
        article_urls = article_urls[:limit]
    print(f"Discovered {len(article_urls)} article page(s) for {code}")

    stored = 0
    with LegInfoClient() as client:
        for index, article_url in enumerate(article_urls, start=1):
            print(f"[{index}/{len(article_urls)}] {article_url}")
            try:
                html, final_url = client.get(article_url)
            except httpx.HTTPError as exc:
                print(f"  [warn] request failed: {exc}")
                continue
            try:
                records = parse_article_page(html, _canonicalize_url(final_url), code)
            except Exception as exc:
                print(f"  [warn] parse failed: {exc}")
                continue
            if not records:
                print("  [skip] no sections found")
                continue
            stored += _save_records(records, jurisdiction_id, "CA")
            print(f"  [ok] stored {len(records)} section(s)")
    print(f"Stored {stored} section(s) for {code}")
    return stored


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", default=DEFAULT_CODE, help="California code abbreviation, e.g. VEH")
    parser.add_argument("--limit", type=int, default=0, help="Maximum article pages to scrape (0 = all)")
    args = parser.parse_args()
    scrape_code(code=args.code.upper(), limit=args.limit)


if __name__ == "__main__":
    main()
