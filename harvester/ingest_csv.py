"""Load eval-ca-vehicle-code.csv into the statutes table + tag rows.

The eval CSV column names are not pinned in the spec, so we detect them at runtime.
Recognised aliases (case-insensitive):

    citation         : citation, cite
    section_number   : section_number, section, section_num, §
    title            : title, statute_title, name
    full_text        : full_text, text, body, statute_text
    source_url       : source_url, url, link
    factor           : contributing_factor, factor, factor_label, category

Constraints (PRD §3.2):
    - source_url and full_text are NOT NULL in the schema. Where the CSV doesn't
      provide them, we insert placeholders + is_verified=0; the scraper fills in
      real values later (and the validator flips is_verified).
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from db.seed import _label_to_code, connect

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = ROOT / "data" / "eval-ca-vehicle-code.csv"
DEFAULT_JURISDICTION = "CA"
PLACEHOLDER_BODY = "[pending scrape]"

COLUMN_ALIASES: dict[str, list[str]] = {
    "citation":       ["citation", "cite", "statute", "universal citation"],
    "section_number": ["section_number", "section", "section_num", "section number", "section #", "§"],
    "title":          ["title", "statute_title", "name"],
    "full_text":      ["full_text", "text", "body", "statute_text", "full text",
                       "complete statute", "statute language"],
    "source_url":     ["source_url", "url", "link", "source url"],
    "factor":         ["contributing_factor", "factor", "factor_label", "category", "contributing factor"],
}

# CA leginfo URL pattern. Subsection markers like "(a)" or "(a)-(b)" must be stripped
# so the request hits the canonical section page (sectionNum=2800.1, not 2800.1(a)).
_SUBSECTION_RE = re.compile(r"\([^)]*\).*$")
CA_LEGINFO_URL = "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=VEH&sectionNum={section}"


def _bare_section(section: str) -> str:
    """Strip "(a)", "(a)-(b)", etc. — keep only the canonical section number."""
    return _SUBSECTION_RE.sub("", section).strip()


def _build_real_url(jurisdiction_code: str, section: str) -> str | None:
    """Return a canonical statute URL for jurisdictions where we know the pattern."""
    if jurisdiction_code == "CA":
        return CA_LEGINFO_URL.format(section=_bare_section(section))
    return None


def _resolve_columns(fieldnames: list[str]) -> dict[str, str | None]:
    lower = {f.lower().strip(): f for f in fieldnames}
    resolved: dict[str, str | None] = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        resolved[canonical] = next((lower[a] for a in aliases if a in lower), None)
    return resolved


_SECTION_RE = re.compile(r"§?\s*([\w\.\-]+)")


def _extract_section(citation: str, fallback: str | None = None) -> str:
    if fallback:
        return fallback.strip()
    m = _SECTION_RE.search(citation.split("§")[-1] if "§" in citation else citation)
    return m.group(1) if m else citation.strip()


def _placeholder_url(base_url: str | None, section: str) -> str:
    return (base_url or "https://example.invalid").rstrip("/") + f"#section-{section}"


def ingest(csv_path: Path = DEFAULT_CSV, jurisdiction_code: str = DEFAULT_JURISDICTION) -> dict:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    stats = {"statutes": 0, "tags": 0, "factors_missing": [], "rows": 0}

    with connect() as conn:
        jur = conn.execute(
            "SELECT id, base_url FROM jurisdictions WHERE code = ?", (jurisdiction_code,)
        ).fetchone()
        if not jur:
            raise RuntimeError(
                f"Jurisdiction '{jurisdiction_code}' not seeded. Run db.seed first."
            )

        with csv_path.open(newline="") as f:
            reader = csv.DictReader(f)
            cols = _resolve_columns(reader.fieldnames or [])
            if not cols["citation"]:
                raise RuntimeError(
                    f"CSV has no recognisable citation column. Headers: {reader.fieldnames}"
                )

            for row in reader:
                stats["rows"] += 1
                citation = (row[cols["citation"]] or "").strip()
                if not citation:
                    continue

                section = _extract_section(
                    citation,
                    fallback=row[cols["section_number"]] if cols["section_number"] else None,
                )
                title = (row[cols["title"]] or "").strip() if cols["title"] else None
                full_text = ((row[cols["full_text"]] or "").strip()
                             if cols["full_text"] else "") or PLACEHOLDER_BODY
                source_url = ((row[cols["source_url"]] or "").strip()
                              if cols["source_url"] else "")
                if not source_url:
                    source_url = (_build_real_url(jurisdiction_code, section)
                                  or _placeholder_url(jur["base_url"], section))

                # Upsert the statute.
                conn.execute(
                    """
                    INSERT INTO statutes
                      (jurisdiction_id, citation, section_number, title, full_text, source_url, is_verified)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                    ON CONFLICT(jurisdiction_id, section_number) DO UPDATE SET
                      citation   = excluded.citation,
                      title      = COALESCE(excluded.title, statutes.title),
                      full_text  = CASE
                          WHEN statutes.full_text = ? THEN excluded.full_text
                          ELSE statutes.full_text
                        END,
                      source_url = CASE
                          WHEN statutes.source_url LIKE 'https://example.invalid%' THEN excluded.source_url
                          ELSE statutes.source_url
                        END
                    """,
                    (jur["id"], citation, section, title, full_text, source_url, PLACEHOLDER_BODY),
                )
                statute_id = conn.execute(
                    "SELECT id FROM statutes WHERE jurisdiction_id = ? AND section_number = ?",
                    (jur["id"], section),
                ).fetchone()["id"]
                stats["statutes"] += 1

                # Tag with the contributing factor if the CSV provided one.
                if cols["factor"]:
                    label = (row[cols["factor"]] or "").strip()
                    if label:
                        code = _label_to_code(label)
                        factor = conn.execute(
                            "SELECT id FROM contributing_factors WHERE code = ? OR label = ?",
                            (code, label),
                        ).fetchone()
                        if not factor:
                            stats["factors_missing"].append(label)
                            continue
                        conn.execute(
                            """
                            INSERT OR IGNORE INTO statute_factor_tags
                              (statute_id, factor_id, confidence, tagged_by)
                            VALUES (?, ?, 1.0, 'manual')
                            """,
                            (statute_id, factor["id"]),
                        )
                        stats["tags"] += 1

        conn.commit()
    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    ap.add_argument("--jurisdiction", default=DEFAULT_JURISDICTION)
    args = ap.parse_args()
    s = ingest(args.csv, jurisdiction_code=args.jurisdiction)
    print(
        f"Rows read: {s['rows']}    statutes upserted: {s['statutes']}    "
        f"tags written: {s['tags']}    factors missing: {len(set(s['factors_missing']))}"
    )
    if s["factors_missing"]:
        print(f"  unknown factor labels (re-run db.seed first?): {sorted(set(s['factors_missing']))}")


if __name__ == "__main__":
    main()
