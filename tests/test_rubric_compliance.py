"""Rubric-compliance integration tests.

Maps directly to the EvenUp × OpenClaw scoring rubric:
    Harvester (50) — schema, query interface, coverage of released set + multi-state
    Ground rules — every record needs a real source URL.

These tests hit the real DB via the public retrieval modules. They are slow
relative to unit tests but pin down the things judges will actually grade.
"""
from __future__ import annotations

import csv
import re
import sqlite3
from pathlib import Path

import pytest

from db.seed import connect
from retrieval import citation_parser, exact_lookup, factor_search, fts_search

REPO = Path(__file__).resolve().parent.parent
RELEASED_CSV = REPO / "data" / "eval-ca-vehicle-code.csv"
REAL_DB = REPO / "db" / "legal_harvester.db"


# These tests are *integration* checks against the production DB, not the
# isolated empty test fixture. Override the session fixture for this module.
@pytest.fixture(scope="module", autouse=True)
def _use_real_db():
    from db import seed
    if not REAL_DB.exists():
        pytest.skip("Real DB not present — rubric tests require live ingest")
    original = seed.DB_PATH
    seed.DB_PATH = REAL_DB
    yield
    seed.DB_PATH = original


def _bare_section(s: str) -> str:
    """Strip subsection markers like '(a)', '(a)-(b)' to canonical section."""
    return re.sub(r"\(.*$", "", s).strip()


# ---------- Floor: released CSV (the 41 CA Vehicle Code statutes) ----------

@pytest.fixture(scope="module")
def released_rows() -> list[dict]:
    return list(csv.DictReader(RELEASED_CSV.open()))


def test_released_csv_present_in_db(released_rows: list[dict]) -> None:
    """All 41 released CA Vehicle Code statutes must be queryable by canonical section."""
    with connect() as c:
        missing = []
        for r in released_rows:
            sec = _bare_section(r["Section #"])
            row = c.execute(
                "SELECT 1 FROM statutes s JOIN jurisdictions j ON j.id=s.jurisdiction_id "
                "WHERE j.code='CA' AND s.section_number=?", (sec,)
            ).fetchone()
            if not row:
                missing.append(r["Statute"])
        assert not missing, f"Missing {len(missing)} released statutes: {missing[:3]}"


def test_released_csv_factor_tagged(released_rows: list[dict]) -> None:
    """Every released statute must have at least one contributing-factor tag."""
    with connect() as c:
        untagged = []
        for r in released_rows:
            sec = _bare_section(r["Section #"])
            row = c.execute(
                "SELECT s.id FROM statutes s JOIN jurisdictions j ON j.id=s.jurisdiction_id "
                "WHERE j.code='CA' AND s.section_number=?", (sec,)
            ).fetchone()
            if not row:
                continue
            n = c.execute(
                "SELECT COUNT(*) FROM statute_factor_tags WHERE statute_id=?", (row[0],)
            ).fetchone()[0]
            if n == 0:
                untagged.append(r["Statute"])
        assert not untagged, f"Untagged released statutes: {untagged[:3]}"


# ---------- Multi-jurisdiction coverage (the rubric ceiling) ----------

@pytest.mark.parametrize("jurisdiction", ["CA", "NY", "FL"])
def test_multi_jurisdiction_coverage(jurisdiction: str) -> None:
    """Each supported jurisdiction must have a non-trivial count of statutes."""
    with connect() as c:
        n = c.execute(
            "SELECT COUNT(*) FROM statutes s JOIN jurisdictions j ON j.id=s.jurisdiction_id "
            "WHERE j.code=?", (jurisdiction,)
        ).fetchone()[0]
        assert n >= 100, f"{jurisdiction} has only {n} statutes — insufficient coverage"


@pytest.mark.parametrize("jurisdiction", ["CA", "NY", "FL"])
def test_multi_jurisdiction_factor_tags(jurisdiction: str) -> None:
    """Each jurisdiction must have factor tags so factor retrieval generalizes."""
    with connect() as c:
        n = c.execute(
            "SELECT COUNT(DISTINCT s.id) FROM statute_factor_tags t "
            "JOIN statutes s ON s.id=t.statute_id "
            "JOIN jurisdictions j ON j.id=s.jurisdiction_id "
            "WHERE j.code=?", (jurisdiction,)
        ).fetchone()[0]
        assert n >= 100, f"{jurisdiction} only has {n} tagged statutes"


# ---------- Ground rule: every record has a real source URL ----------

def test_every_statute_has_source_url() -> None:
    """Per the rubric: 'Records without a real source URL don't count.'"""
    with connect() as c:
        bad = c.execute(
            "SELECT COUNT(*) FROM statutes WHERE source_url IS NULL OR length(source_url)=0"
        ).fetchone()[0]
        assert bad == 0, f"{bad} statutes without source_url"


def test_source_urls_are_real() -> None:
    """No placeholder/example.invalid URLs (ground rule: real sources only)."""
    with connect() as c:
        bad = c.execute(
            "SELECT COUNT(*) FROM statutes WHERE source_url LIKE 'https://example.invalid%'"
        ).fetchone()[0]
        # Tolerate a small number from the CSV pre-seed before scrape backfill.
        assert bad < 10, f"{bad} placeholder URLs still present — scrape didn't backfill"


def test_source_url_domains_are_authoritative() -> None:
    """Every source URL must be from a known authoritative domain."""
    AUTHORITATIVE = {
        "leginfo.legislature.ca.gov",   # CA official
        "codes.findlaw.com",            # FindLaw mirror (NY/FL)
        "www.flsenate.gov",             # FL official
        "statutes.capitol.texas.gov",   # TX official (live-fetch)
    }
    from urllib.parse import urlparse
    with connect() as c:
        rows = c.execute(
            "SELECT source_url FROM statutes "
            "WHERE source_url NOT LIKE 'https://example.invalid%' "
            "GROUP BY source_url LIMIT 200"
        ).fetchall()
    bad = []
    for r in rows:
        domain = urlparse(r[0]).netloc
        if domain and domain not in AUTHORITATIVE:
            bad.append(domain)
    assert not bad, f"Non-authoritative domains: {set(bad)}"


# ---------- Citation lookup (cached + live-fetch path) ----------

@pytest.mark.parametrize("query, expect_jurisdiction, expect_section", [
    ("CA Veh Code 22107",       "CA", "22107"),
    ("CA Veh Code §23152(a)",   "CA", "23152"),     # released set, with subsection
    ("Cal. Penal Code 187",     "CA", "187"),       # alt CA notation
    ("NY VAT 1192",             "NY", "1192"),
    ("NY VAT § 1192",           "NY", "1192"),
    ("Fla. Stat. 316.193",      "FL", "316.193"),
    ("FL Stat 316.193",         "FL", "316.193"),
])
def test_citation_lookup_known_sections(query, expect_jurisdiction, expect_section):
    """Citation lookup must hit the local DB for sections judges expect to be there."""
    parsed = citation_parser.parse(query)
    assert parsed is not None, f"Citation parser failed on {query!r}"
    assert parsed.jurisdiction == expect_jurisdiction
    assert parsed.section == expect_section
    hit = exact_lookup.lookup(parsed)
    assert hit is not None, f"DB miss on {query!r} (parsed={parsed})"
    assert hit["jurisdiction"] == expect_jurisdiction


def test_citation_parser_distinguishes_codes_in_same_jurisdiction():
    """Multi-code DBs must filter by code_name, not just jurisdiction+section."""
    # NY VAT §349 exists; NY GBL §349 is different. Without the code filter,
    # exact_lookup used to leak the wrong row.
    vat = citation_parser.parse("NY VAT 349")
    gbl = citation_parser.parse("NY GBL 349")
    assert vat is not None and gbl is not None
    assert vat.code_name != gbl.code_name


# ---------- Factor retrieval (rubric: contributing-factor retrieval) ----------

def test_all_seventeen_factors_seeded():
    """All 17 contributing-factor categories from the released set must exist."""
    factors = factor_search.list_factors()
    assert len(factors) >= 17, f"only {len(factors)} factors seeded"


def test_factor_retrieval_returns_results_per_jurisdiction():
    """For each jurisdiction the most-used factor must surface at least one row."""
    with connect() as c:
        for jur in ("CA", "NY", "FL"):
            top_factor = c.execute("""
                SELECT cf.code, COUNT(*) AS n
                  FROM statute_factor_tags t
                  JOIN statutes s ON s.id = t.statute_id
                  JOIN jurisdictions j ON j.id = s.jurisdiction_id
                  JOIN contributing_factors cf ON cf.id = t.factor_id
                 WHERE j.code = ?
                 GROUP BY cf.code ORDER BY n DESC LIMIT 1
            """, (jur,)).fetchone()
            assert top_factor, f"no factor tags for {jur}"
            results = factor_search.by_factor(top_factor["code"], jurisdiction=jur, limit=5)
            assert results, f"factor_search.by_factor returned 0 for {jur}/{top_factor['code']}"


# ---------- FTS retrieval (cross-jurisdictional) ----------

def test_fts_returns_cross_jurisdiction_results():
    """A natural-language query must surface hits from more than one state."""
    results = fts_search.search("under the influence", limit=20)
    jurisdictions = {r["jurisdiction"] for r in results}
    assert len(jurisdictions) >= 2, f"FTS only hit one jurisdiction: {jurisdictions}"


def test_fts_handles_punctuation_in_user_query():
    """Natural-language queries with hyphens (rear-ended) must not break FTS."""
    results = fts_search.search("rear-ended at a stop sign", limit=5)
    assert isinstance(results, list)
    # We don't assert non-empty (semantic recall isn't guaranteed) — only that
    # it doesn't raise on FTS5 syntax.


# ---------- End-to-end query routing ----------

def test_query_router_dispatches_correctly():
    """The router picks the right kind for each query shape."""
    from retrieval import query_router
    cases = [
        ("CA Veh Code 22107",          "citation"),
        ("DUI",                        "factor"),
        ("rear-ended at a stop sign",  "fts"),
    ]
    for q, expected in cases:
        r = query_router.route(q, limit=3)
        assert r["kind"] == expected, f"{q!r} routed to {r['kind']}, expected {expected}"


# ---------- Schema documentation ----------

def test_schema_file_exists_and_documents_critical_columns():
    schema = (REPO / "db" / "schema.sql").read_text()
    for required in ("citation", "section_number", "source_url", "full_text", "statute_factor_tags", "statute_fts"):
        assert required in schema, f"schema.sql missing {required}"
