# CSV Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `harvester/ingest_csv.py` so it loads `data/eval-ca-vehicle-code.csv` into SQLite with skip-on-conflict deduplication and ground-truth factor tagging from the CSV's `Contributing Factor` column.

**Architecture:** Single Python module (`harvester/ingest_csv.py`) drives the whole pipeline: validate CSV columns up front, normalize per-row values via small dicts (`STATE_TO_CODE`, `CITATION_TO_CODE_NAME`, `CSV_FACTOR_TO_SLUG`), `INSERT OR IGNORE` into `statutes` and `factors`, then link via `statute_factors`. Tests in `tests/test_ingest_csv.py` use the existing session-scoped `_isolated_db` fixture from `conftest.py` and a per-test cleanup fixture so each test starts with empty `statutes`.

**Tech Stack:** Python 3.9 (stdlib only — `csv`, `re`, `sqlite3`, `pathlib`, `argparse`, `json`), pytest. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-05-09-csv-ingestion-design.md`

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `harvester/ingest_csv.py` | Modify (full rewrite) | The ingestion module: column normalization, statute insert with dedup, factor resolution + auto-create, source_url construction, CLI entry. |
| `tests/test_ingest_csv.py` | Create | All ingestion tests: slugify, column validation, mapping, dedup, factors, source_url, errors. |
| `tests/test_eval_coverage.py` | Modify (1 line) | Update assertion to match new dict return shape. |
| `Roadmap.txt` | Modify | After Task 6, mark roadmap items 6, 7, 8 as `[x]` done. |

All ingestion-specific knowledge (column names, value normalization dicts, factor mapping) lives in one file — `harvester/ingest_csv.py` — so changes to the CSV format only require editing one place.

---

## Task 1: Slugify helper + test scaffolding

**Files:**
- Create: `tests/test_ingest_csv.py`
- Modify: `harvester/ingest_csv.py` (add `slugify`, keep existing function untouched for now)

- [ ] **Step 1: Write the failing tests**

Create `tests/test_ingest_csv.py`:

```python
"""Tests for harvester.ingest_csv."""
from __future__ import annotations

import pytest

from db.seed import connect

# Slugs of factors seeded by db.seed.DEFAULT_FACTORS. The reset fixture preserves
# these and deletes anything else, so per-test auto-create counts are deterministic
# regardless of which other test files ran first.
SEEDED_SLUGS = (
    "dui", "failure_to_yield", "speeding", "distracted_driving",
    "following_too_close", "unsafe_lane_change", "running_red_light",
    "reckless_driving",
)


@pytest.fixture(autouse=True)
def _reset_ingest_state():
    """Each test starts with empty statutes/statute_factors and only the
    8 seeded factors. Auto-created factors from prior tests are removed."""
    with connect() as conn:
        conn.execute("DELETE FROM statute_factors")
        conn.execute("DELETE FROM statutes")
        placeholders = ",".join("?" * len(SEEDED_SLUGS))
        conn.execute(
            f"DELETE FROM factors WHERE slug NOT IN ({placeholders})",
            SEEDED_SLUGS,
        )
        conn.commit()
    yield


def test_slugify_basic():
    from harvester.ingest_csv import slugify
    assert slugify("Improper Turning") == "improper_turning"


def test_slugify_punctuation():
    from harvester.ingest_csv import slugify
    assert slugify("DUI/DWI") == "dui_dwi"


def test_slugify_collapses_runs_and_strips_edges():
    from harvester.ingest_csv import slugify
    assert slugify("  Failure -- to  Yield!  ") == "failure_to_yield"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_ingest_csv.py -v`

Expected: 3 ImportError or AttributeError failures — `slugify` does not exist in `harvester.ingest_csv` yet.

- [ ] **Step 3: Add `slugify` to `harvester/ingest_csv.py`**

Add at the top of `harvester/ingest_csv.py`, just after the existing imports (do NOT modify the existing `ingest`/`main`/`DEFAULT_CSV` yet — those get rewritten in Task 3):

```python
import re
```

Then add this function above `ingest`:

```python
def slugify(label: str) -> str:
    """lowercase → replace non-alnum runs with `_` → strip leading/trailing `_`."""
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_ingest_csv.py -v`

Expected: 3 passed.

Run the full suite to confirm nothing else broke:

Run: `.venv/bin/python -m pytest -q`

Expected: 9 passed, 1 skipped (test_eval_coverage skipped only if CSV missing — with CSV present it will FAIL on the existing ingest() because of column mismatch; that's expected and gets fixed in Task 3).

If `test_ingest_loads_all_rows` fails with `KeyError: 'section'`, that is the expected pre-Task-3 state. Continue.

- [ ] **Step 5: Commit**

```bash
git add tests/test_ingest_csv.py harvester/ingest_csv.py
git commit -m "Add slugify helper and ingest test scaffolding"
```

---

## Task 2: Column validation helper

**Files:**
- Modify: `harvester/ingest_csv.py` (add `REQUIRED_COLUMNS`, `_validate_columns`)
- Modify: `tests/test_ingest_csv.py` (add validation tests)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_ingest_csv.py`:

```python
def test_validate_columns_passes_with_all_required():
    from harvester.ingest_csv import _validate_columns, REQUIRED_COLUMNS
    _validate_columns(list(REQUIRED_COLUMNS))  # must not raise


def test_validate_columns_raises_on_missing():
    from harvester.ingest_csv import _validate_columns
    with pytest.raises(ValueError, match="missing required column"):
        _validate_columns(["State", "Section #"])


def test_validate_columns_raises_on_none():
    from harvester.ingest_csv import _validate_columns
    with pytest.raises(ValueError, match="missing required column"):
        _validate_columns(None)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_ingest_csv.py::test_validate_columns_passes_with_all_required tests/test_ingest_csv.py::test_validate_columns_raises_on_missing tests/test_ingest_csv.py::test_validate_columns_raises_on_none -v`

Expected: 3 ImportError failures — `REQUIRED_COLUMNS` and `_validate_columns` not defined.

- [ ] **Step 3: Add `REQUIRED_COLUMNS` and `_validate_columns`**

In `harvester/ingest_csv.py`, just below `slugify`, add:

```python
REQUIRED_COLUMNS = (
    "Statute",
    "State",
    "Universal Citation",
    "Section #",
    "Statute Language",
    "Contributing Factor",
)


def _validate_columns(fieldnames):
    missing = [c for c in REQUIRED_COLUMNS if c not in (fieldnames or [])]
    if missing:
        raise ValueError(
            f"CSV missing required column(s): {', '.join(missing)}"
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_ingest_csv.py -v`

Expected: 6 passed (3 slugify + 3 validation).

- [ ] **Step 5: Commit**

```bash
git add tests/test_ingest_csv.py harvester/ingest_csv.py
git commit -m "Add CSV column validation helper"
```

---

## Task 3: Rewrite ingest() — column mapping, dedup, dict return, error handling

**Files:**
- Modify: `harvester/ingest_csv.py` (replace `ingest` and `main`)
- Modify: `tests/test_ingest_csv.py` (add ingest tests)
- Modify: `tests/test_eval_coverage.py` (update assertion shape)

This is the biggest task. After it, the function fully handles the statute table. Factors and source_url come in Tasks 4 and 5.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_ingest_csv.py`:

```python
HEADER = (
    "Statute,State,Universal Citation,Section #,"
    "Statute Language,Complete Statute,Contributing Factor"
)


def _write_csv(path, rows):
    """rows is a list of dicts keyed by header column."""
    cols = HEADER.split(",")
    lines = [HEADER]
    for r in rows:
        # Quote fields containing commas/quotes
        vals = []
        for c in cols:
            v = r.get(c, "")
            if "," in v or '"' in v:
                v = '"' + v.replace('"', '""') + '"'
            vals.append(v)
        lines.append(",".join(vals))
    path.write_text("\n".join(lines) + "\n")


def test_ingest_returns_summary_dict(tmp_path):
    from harvester.ingest_csv import ingest
    csv = tmp_path / "t.csv"
    _write_csv(csv, [{
        "Statute": "Cal. Veh. Code § 99001",
        "State": "California",
        "Universal Citation": "Cal. Veh. Code",
        "Section #": "99001",
        "Statute Language": "test body",
        "Complete Statute": "full",
        "Contributing Factor": "DUI/DWI",
    }])
    result = ingest(csv)
    assert set(result.keys()) == {
        "inserted", "skipped", "factors_created", "statute_factor_links"
    }
    assert result["inserted"] == 1
    assert result["skipped"] == 0


def test_ingest_normalizes_state_and_citation(tmp_path):
    from harvester.ingest_csv import ingest
    csv = tmp_path / "t.csv"
    _write_csv(csv, [{
        "Statute": "Cal. Veh. Code § 99002",
        "State": "California",
        "Universal Citation": "Cal. Veh. Code",
        "Section #": "99002",
        "Statute Language": "body two",
        "Complete Statute": "full",
        "Contributing Factor": "Reckless Driving",
    }])
    ingest(csv)
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM statutes WHERE section='99002'"
        ).fetchone()
    assert row["jurisdiction"] == "CA"
    assert row["code_name"] == "Vehicle Code"
    assert row["body"] == "body two"
    assert row["title"] == "Cal. Veh. Code § 99002"


def test_ingest_skip_on_conflict(tmp_path):
    from harvester.ingest_csv import ingest
    csv = tmp_path / "t.csv"
    _write_csv(csv, [{
        "Statute": "Cal. Veh. Code § 99003",
        "State": "California",
        "Universal Citation": "Cal. Veh. Code",
        "Section #": "99003",
        "Statute Language": "body",
        "Complete Statute": "full",
        "Contributing Factor": "DUI/DWI",
    }])
    first = ingest(csv)
    second = ingest(csv)
    assert first["inserted"] == 1
    assert second["inserted"] == 0
    assert second["skipped"] == 1
    with connect() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM statutes WHERE section='99003'"
        ).fetchone()["c"]
    assert count == 1


def test_ingest_raises_on_unknown_state(tmp_path):
    from harvester.ingest_csv import ingest
    csv = tmp_path / "t.csv"
    _write_csv(csv, [{
        "Statute": "X",
        "State": "Atlantis",
        "Universal Citation": "Cal. Veh. Code",
        "Section #": "99004",
        "Statute Language": "body",
        "Complete Statute": "full",
        "Contributing Factor": "DUI/DWI",
    }])
    with pytest.raises(ValueError, match="unknown State"):
        ingest(csv)


def test_ingest_raises_on_unknown_citation(tmp_path):
    from harvester.ingest_csv import ingest
    csv = tmp_path / "t.csv"
    _write_csv(csv, [{
        "Statute": "X",
        "State": "California",
        "Universal Citation": "Made Up Code",
        "Section #": "99005",
        "Statute Language": "body",
        "Complete Statute": "full",
        "Contributing Factor": "DUI/DWI",
    }])
    with pytest.raises(ValueError, match="unknown Universal Citation"):
        ingest(csv)


def test_ingest_raises_on_empty_body(tmp_path):
    from harvester.ingest_csv import ingest
    csv = tmp_path / "t.csv"
    _write_csv(csv, [{
        "Statute": "X",
        "State": "California",
        "Universal Citation": "Cal. Veh. Code",
        "Section #": "99006",
        "Statute Language": "",
        "Complete Statute": "full",
        "Contributing Factor": "DUI/DWI",
    }])
    with pytest.raises(ValueError, match="empty Statute Language"):
        ingest(csv)


def test_ingest_raises_on_missing_csv():
    from harvester.ingest_csv import ingest
    with pytest.raises(FileNotFoundError):
        ingest(tmp_path_that_does_not_exist())


def tmp_path_that_does_not_exist():
    from pathlib import Path
    return Path("/nonexistent/path/to/file.csv")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_ingest_csv.py -v`

Expected: existing 6 still pass (slugify + validation); the 7 new ingest tests fail because the existing `ingest` returns an `int`, not a dict, and crashes on column lookup with the new CSV columns.

- [ ] **Step 3: Replace the entire `harvester/ingest_csv.py` body**

This task fully replaces the file from `DEFAULT_CSV` downward. The slugify, REQUIRED_COLUMNS, and _validate_columns added in Tasks 1 and 2 are kept. The complete file should now read:

```python
"""Load eval-ca-vehicle-code.csv into the statutes table.

Loads CSV with these columns:
    Statute, State, Universal Citation, Section #,
    Statute Language, Complete Statute, Contributing Factor

Skip-on-conflict deduplication: rows whose (jurisdiction, code_name, section)
already exists are left untouched. Factors and source_url are added in
later tasks of the implementation plan.
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from db.seed import connect

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = ROOT / "data" / "eval-ca-vehicle-code.csv"

STATE_TO_CODE = {
    "California": "CA",
}

CITATION_TO_CODE_NAME = {
    "Cal. Veh. Code": "Vehicle Code",
}

REQUIRED_COLUMNS = (
    "Statute",
    "State",
    "Universal Citation",
    "Section #",
    "Statute Language",
    "Contributing Factor",
)


def slugify(label: str) -> str:
    """lowercase → replace non-alnum runs with `_` → strip leading/trailing `_`."""
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


def _validate_columns(fieldnames):
    missing = [c for c in REQUIRED_COLUMNS if c not in (fieldnames or [])]
    if missing:
        raise ValueError(
            f"CSV missing required column(s): {', '.join(missing)}"
        )


def _normalize_row(row: dict, row_num: int) -> dict:
    """Return a dict of normalized DB-shaped values for a single CSV row.
    Raises ValueError with the row number if any required field is bad."""
    state = (row.get("State") or "").strip()
    citation = (row.get("Universal Citation") or "").strip()
    section = (row.get("Section #") or "").strip()
    body = (row.get("Statute Language") or "").strip()
    title = (row.get("Statute") or "").strip() or None

    jurisdiction = STATE_TO_CODE.get(state)
    if jurisdiction is None:
        raise ValueError(f"row {row_num}: unknown State '{state}'")
    code_name = CITATION_TO_CODE_NAME.get(citation)
    if code_name is None:
        raise ValueError(
            f"row {row_num}: unknown Universal Citation '{citation}'"
        )
    if not section:
        raise ValueError(f"row {row_num}: empty Section #")
    if not body:
        raise ValueError(f"row {row_num}: empty Statute Language")

    return {
        "jurisdiction": jurisdiction,
        "code_name": code_name,
        "section": section,
        "title": title,
        "body": body,
    }


def ingest(csv_path: Path = DEFAULT_CSV) -> dict:
    """Load CSV into statutes with skip-on-conflict dedup. Returns a summary."""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    inserted = 0
    skipped = 0

    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        _validate_columns(reader.fieldnames)
        rows = list(reader)

    with connect() as conn:
        for i, raw in enumerate(rows, start=2):  # start=2: header is row 1
            n = _normalize_row(raw, i)
            cur = conn.execute(
                """INSERT OR IGNORE INTO statutes
                       (jurisdiction, code_name, section, title, body,
                        source_url, effective_date)
                   VALUES (?, ?, ?, ?, ?, NULL, NULL)""",
                (n["jurisdiction"], n["code_name"], n["section"],
                 n["title"], n["body"]),
            )
            if cur.rowcount == 1:
                inserted += 1
            else:
                skipped += 1
        conn.commit()

    return {
        "inserted": inserted,
        "skipped": skipped,
        "factors_created": 0,        # populated in Task 4
        "statute_factor_links": 0,   # populated in Task 4
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    args = ap.parse_args()
    r = ingest(args.csv)
    print(
        f"inserted={r['inserted']}  skipped={r['skipped']}  "
        f"factors_created={r['factors_created']}  "
        f"statute_factor_links={r['statute_factor_links']}"
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Update `tests/test_eval_coverage.py` for the new return shape**

Replace the body of `tests/test_eval_coverage.py` with:

```python
"""Smoke test: when data/eval-ca-vehicle-code.csv is present, ingest covers every row."""
from pathlib import Path

import pytest

from db.seed import connect
from harvester.ingest_csv import DEFAULT_CSV, ingest


@pytest.mark.skipif(not DEFAULT_CSV.exists(), reason="eval CSV not provided")
def test_ingest_loads_all_rows():
    result = ingest(DEFAULT_CSV)
    inserted = result["inserted"]
    skipped = result["skipped"]
    # Roadmap item 8: assert all 41 citations present.
    assert inserted + skipped == 41, (
        f"expected 41 CSV rows processed, got inserted={inserted} skipped={skipped}"
    )
    with connect() as conn:
        ca_count = conn.execute(
            "SELECT COUNT(*) AS c FROM statutes "
            "WHERE jurisdiction='CA' AND code_name='Vehicle Code'"
        ).fetchone()["c"]
    assert ca_count >= 41
```

- [ ] **Step 5: Run all tests to verify they pass**

Run: `.venv/bin/python -m pytest -q`

Expected: 13 passed (or so — 3 slugify + 3 validation + 7 ingest + 4 from other test files), 0 skipped (test_eval_coverage now runs because the CSV is present and the function works).

If `test_eval_coverage` fails with `unknown State 'California'` or similar, double-check the `STATE_TO_CODE` dict.

- [ ] **Step 6: Commit**

```bash
git add tests/test_ingest_csv.py tests/test_eval_coverage.py harvester/ingest_csv.py
git commit -m "Rewrite ingest_csv for new schema with skip-on-conflict dedup"
```

---

## Task 4: Factor mapping (curated dict + auto-create + linkage)

**Files:**
- Modify: `harvester/ingest_csv.py` (add `CSV_FACTOR_TO_SLUG`, factor resolution, factor linkage)
- Modify: `tests/test_ingest_csv.py` (add factor tests)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_ingest_csv.py`:

```python
def test_factor_reuse_seeded_dui(tmp_path):
    """CSV label 'DUI/DWI' must link to the seeded `dui` factor without
    creating a new factor row."""
    from harvester.ingest_csv import ingest
    csv = tmp_path / "t.csv"
    _write_csv(csv, [{
        "Statute": "X",
        "State": "California",
        "Universal Citation": "Cal. Veh. Code",
        "Section #": "99100",
        "Statute Language": "body",
        "Complete Statute": "full",
        "Contributing Factor": "DUI/DWI",
    }])
    result = ingest(csv)
    assert result["factors_created"] == 0
    assert result["statute_factor_links"] == 1
    with connect() as conn:
        row = conn.execute(
            """SELECT f.slug FROM statute_factors sf
               JOIN factors f ON f.id = sf.factor_id
               JOIN statutes s ON s.id = sf.statute_id
               WHERE s.section='99100'"""
        ).fetchone()
    assert row["slug"] == "dui"


def test_factor_auto_create_unmapped(tmp_path):
    """An unmapped CSV label creates a new factor row with slug=slugify(label)."""
    from harvester.ingest_csv import ingest
    csv = tmp_path / "t.csv"
    _write_csv(csv, [{
        "Statute": "X",
        "State": "California",
        "Universal Citation": "Cal. Veh. Code",
        "Section #": "99101",
        "Statute Language": "body",
        "Complete Statute": "full",
        "Contributing Factor": "Improper Turning",
    }])
    result = ingest(csv)
    assert result["factors_created"] == 1
    assert result["statute_factor_links"] == 1
    with connect() as conn:
        row = conn.execute(
            "SELECT slug, label FROM factors WHERE slug='improper_turning'"
        ).fetchone()
    assert row is not None
    assert row["label"] == "Improper Turning"


def test_factor_slug_collapse(tmp_path):
    """Two CSV labels mapped to the same slug yield ONE factor row but TWO
    statute_factors rows."""
    from harvester.ingest_csv import ingest
    csv = tmp_path / "t.csv"
    _write_csv(csv, [
        {
            "Statute": "X1",
            "State": "California",
            "Universal Citation": "Cal. Veh. Code",
            "Section #": "99102",
            "Statute Language": "body1",
            "Complete Statute": "full",
            "Contributing Factor": "Failure to Yield at a Yield Sign",
        },
        {
            "Statute": "X2",
            "State": "California",
            "Universal Citation": "Cal. Veh. Code",
            "Section #": "99103",
            "Statute Language": "body2",
            "Complete Statute": "full",
            "Contributing Factor": "Failure to Yield the Right-of-Way",
        },
    ])
    result = ingest(csv)
    assert result["statute_factor_links"] == 2
    with connect() as conn:
        slugs = conn.execute(
            """SELECT DISTINCT f.slug FROM statute_factors sf
               JOIN factors f ON f.id = sf.factor_id
               JOIN statutes s ON s.id = sf.statute_id
               WHERE s.section IN ('99102','99103')"""
        ).fetchall()
    assert len(slugs) == 1
    assert slugs[0]["slug"] == "failure_to_yield"


def test_factor_idempotent_on_rerun(tmp_path):
    """Running ingest twice does not duplicate statute_factors rows."""
    from harvester.ingest_csv import ingest
    csv = tmp_path / "t.csv"
    _write_csv(csv, [{
        "Statute": "X",
        "State": "California",
        "Universal Citation": "Cal. Veh. Code",
        "Section #": "99104",
        "Statute Language": "body",
        "Complete Statute": "full",
        "Contributing Factor": "Improper Turning",
    }])
    ingest(csv)
    second = ingest(csv)
    assert second["inserted"] == 0
    assert second["skipped"] == 1
    assert second["statute_factor_links"] == 0
    with connect() as conn:
        count = conn.execute(
            """SELECT COUNT(*) AS c FROM statute_factors sf
               JOIN statutes s ON s.id = sf.statute_id
               WHERE s.section='99104'"""
        ).fetchone()["c"]
    assert count == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_ingest_csv.py -v -k factor`

Expected: 4 failures — `factors_created` and `statute_factor_links` are still hardcoded to 0 in the return dict, and no factor logic runs.

- [ ] **Step 3: Add factor resolution + linkage to `harvester/ingest_csv.py`**

Below `CITATION_TO_CODE_NAME`, add the curated mapping:

```python
CSV_FACTOR_TO_SLUG = {
    "DUI/DWI": "dui",
    "Following Too Closely": "following_too_close",
    "Reckless Driving": "reckless_driving",
    "Using a Wireless Telephone/Texting While Driving": "distracted_driving",
    "Driving Too Fast For Conditions": "speeding",
    "Failure to Yield at a Yield Sign": "failure_to_yield",
    "Failure to Yield the Right-of-Way": "failure_to_yield",
}
```

Add this helper just below `_normalize_row`:

```python
def _resolve_factor(conn, label: str) -> tuple[int, bool]:
    """Return (factor_id, created) for the CSV label.

    Uses CSV_FACTOR_TO_SLUG when present, else slugify(label). New factor rows
    are auto-created with empty keywords ('[]') so the keyword classifier
    keeps working on seeded factors and ignores CSV-derived ones."""
    slug = CSV_FACTOR_TO_SLUG.get(label, slugify(label))
    cur = conn.execute(
        "INSERT OR IGNORE INTO factors(slug, label, keywords) VALUES (?, ?, '[]')",
        (slug, label),
    )
    created = cur.rowcount == 1
    row = conn.execute(
        "SELECT id FROM factors WHERE slug = ?", (slug,)
    ).fetchone()
    return row["id"], created
```

Update `ingest()` to call factor resolution and linkage. Replace the
`with connect() as conn:` block in `ingest()` with:

```python
    factors_created = 0
    statute_factor_links = 0

    with connect() as conn:
        for i, raw in enumerate(rows, start=2):
            n = _normalize_row(raw, i)
            cur = conn.execute(
                """INSERT OR IGNORE INTO statutes
                       (jurisdiction, code_name, section, title, body,
                        source_url, effective_date)
                   VALUES (?, ?, ?, ?, ?, NULL, NULL)""",
                (n["jurisdiction"], n["code_name"], n["section"],
                 n["title"], n["body"]),
            )
            if cur.rowcount == 1:
                inserted += 1
            else:
                skipped += 1

            # Look up the statute id (works whether we just inserted or it existed)
            statute_id = conn.execute(
                """SELECT id FROM statutes
                   WHERE jurisdiction=? AND code_name=? AND section=?""",
                (n["jurisdiction"], n["code_name"], n["section"]),
            ).fetchone()["id"]

            # Skip factor work for rows that were already in the DB (idempotent)
            if cur.rowcount != 1:
                continue

            label = (raw.get("Contributing Factor") or "").strip()
            if not label:
                continue
            factor_id, created = _resolve_factor(conn, label)
            if created:
                factors_created += 1
            link = conn.execute(
                """INSERT OR IGNORE INTO statute_factors
                       (statute_id, factor_id, confidence)
                   VALUES (?, ?, 1.0)""",
                (statute_id, factor_id),
            )
            if link.rowcount == 1:
                statute_factor_links += 1
        conn.commit()
```

Update the return value of `ingest()` to use the real counts:

```python
    return {
        "inserted": inserted,
        "skipped": skipped,
        "factors_created": factors_created,
        "statute_factor_links": statute_factor_links,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_ingest_csv.py -v`

Expected: all factor tests pass, plus all earlier tests still green.

Run: `.venv/bin/python -m pytest -q`

Expected: full suite green, 0 skipped.

- [ ] **Step 5: Commit**

```bash
git add tests/test_ingest_csv.py harvester/ingest_csv.py
git commit -m "Add factor mapping with curated dict and auto-create"
```

---

## Task 5: source_url construction from registry

**Files:**
- Modify: `harvester/ingest_csv.py` (add `_build_source_url`, wire into ingest)
- Modify: `tests/test_ingest_csv.py` (add source_url tests)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_ingest_csv.py`:

```python
def test_source_url_built_from_registry(tmp_path):
    """For known (jurisdiction, code_name) pairs, source_url is built from
    data/source_registry.json."""
    from harvester.ingest_csv import ingest
    csv = tmp_path / "t.csv"
    _write_csv(csv, [{
        "Statute": "X",
        "State": "California",
        "Universal Citation": "Cal. Veh. Code",
        "Section #": "99200",
        "Statute Language": "body",
        "Complete Statute": "full",
        "Contributing Factor": "DUI/DWI",
    }])
    ingest(csv)
    with connect() as conn:
        row = conn.execute(
            "SELECT source_url FROM statutes WHERE section='99200'"
        ).fetchone()
    # Expect URL with the section interpolated
    assert row["source_url"] is not None
    assert "99200" in row["source_url"]
    assert row["source_url"].startswith(
        "https://leginfo.legislature.ca.gov/"
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_ingest_csv.py::test_source_url_built_from_registry -v`

Expected: assertion failure on `row["source_url"] is not None` because Task 3 inserts NULL for source_url.

- [ ] **Step 3: Add `_build_source_url` and wire it in**

In `harvester/ingest_csv.py`, near the imports add:

```python
import json
```

Below `DEFAULT_CSV`, add:

```python
SOURCE_REGISTRY_PATH = ROOT / "data" / "source_registry.json"
```

Add this helper just below `_resolve_factor`:

```python
def _build_source_url(jurisdiction: str, code_name: str, section: str) -> str | None:
    """Return a URL built from data/source_registry.json, or None if the
    (jurisdiction, code_name) pair is unregistered."""
    try:
        registry = json.loads(SOURCE_REGISTRY_PATH.read_text())
    except FileNotFoundError:
        return None
    entry = registry.get(jurisdiction, {}).get(code_name)
    if not entry:
        return None
    return entry["base_url"] + entry["query_template"].format(section=section)
```

In `ingest()`, replace the `INSERT OR IGNORE INTO statutes` call with:

```python
            source_url = _build_source_url(
                n["jurisdiction"], n["code_name"], n["section"]
            )
            cur = conn.execute(
                """INSERT OR IGNORE INTO statutes
                       (jurisdiction, code_name, section, title, body,
                        source_url, effective_date)
                   VALUES (?, ?, ?, ?, ?, ?, NULL)""",
                (n["jurisdiction"], n["code_name"], n["section"],
                 n["title"], n["body"], source_url),
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest -q`

Expected: full suite green.

- [ ] **Step 5: Commit**

```bash
git add tests/test_ingest_csv.py harvester/ingest_csv.py
git commit -m "Build source_url from source_registry.json during ingest"
```

---

## Task 6: End-to-end verification + roadmap update

**Files:**
- Modify: `Roadmap.txt` (mark items 6, 7, 8 as `[x]`)

This task is verification-only against the real CSV — no new code. Records actual outputs so the implementation is provably done.

- [ ] **Step 1: Reset the local DB to a clean state**

```bash
rm -f db/legal_harvester.db
.venv/bin/python -m db.seed
```

Expected: `Initialized /Users/erinhorner/Christopher/TrialTitans/db/legal_harvester.db`

- [ ] **Step 2: Run the real ingestion (first run)**

Run: `.venv/bin/python -m harvester.ingest_csv`

Expected output line:
```
inserted=41  skipped=0  factors_created=<N>  statute_factor_links=41
```
where `<N>` is the count of CSV factor labels not already covered by the curated dict's mapping to a seeded slug.

- [ ] **Step 3: Run the ingestion a second time (idempotency check)**

Run: `.venv/bin/python -m harvester.ingest_csv`

Expected output line:
```
inserted=0  skipped=41  factors_created=0  statute_factor_links=0
```

- [ ] **Step 4: Rebuild FTS index**

Run: `.venv/bin/python -m harvester.build_fts_index`

Expected: `FTS index rebuilt with 41 rows`

- [ ] **Step 5: SQL spot-checks**

Run:

```bash
.venv/bin/python -c "
from db.seed import connect
with connect() as conn:
    n = conn.execute('SELECT COUNT(*) AS c FROM statutes').fetchone()['c']
    print(f'statutes: {n}')
    by_jur = conn.execute(
        \"SELECT jurisdiction, COUNT(*) AS c FROM statutes GROUP BY jurisdiction\"
    ).fetchall()
    for r in by_jur: print(f'  {r[\"jurisdiction\"]}: {r[\"c\"]}')
    print('factors:')
    rows = conn.execute(
        '''SELECT f.slug, COUNT(*) AS c FROM statute_factors sf
           JOIN factors f ON f.id = sf.factor_id
           GROUP BY f.slug ORDER BY c DESC, f.slug'''
    ).fetchall()
    for r in rows: print(f'  {r[\"slug\"]:35s}  {r[\"c\"]}')
"
```

Expected:
- `statutes: 41`
- `CA: 41`
- A list of factor slugs with per-factor counts summing to 41 (some statutes share factors via the slug-collapse).

- [ ] **Step 6: Run the full test suite**

Run: `.venv/bin/python -m pytest -v`

Expected: all tests pass, 0 skipped.

- [ ] **Step 7: Update Roadmap.txt**

In `Roadmap.txt`, change the `[~]` markers on items 6, 7, 8 to `[x]`, and update the trailing description from `IN PROGRESS` to `DONE 2026-05-09`.

- [ ] **Step 8: Final commit**

```bash
git add Roadmap.txt
git commit -m "Mark CSV ingestion roadmap items complete"
```

- [ ] **Step 9: Report results**

Reply to the user with the actual numbers from Step 2's output (factors_created, statute_factor_links) and Step 5's factor distribution. Do NOT claim success without these numbers.

---

## Self-Review Notes

**Spec coverage:** every section of `docs/superpowers/specs/2026-05-09-csv-ingestion-design.md` maps to a task — column mapping (Task 3), dedup (Task 3), curated factor mapping (Task 4), source_url with NULL fallback (Task 5), strict error handling (Task 3), public API dict (Task 3), tests as listed in spec (Tasks 1–5), verification (Task 6).

**Placeholder scan:** every code block contains the literal code to write. Commands are concrete. No "TBD", no "implement appropriately."

**Type consistency:** `ingest()` returns `dict` everywhere. `slugify(label) -> str`, `_validate_columns(fieldnames) -> None`, `_normalize_row(row, row_num) -> dict`, `_resolve_factor(conn, label) -> tuple[int, bool]`, `_build_source_url(jur, code, section) -> str | None`. Test fixture helper `_write_csv(path, rows)` is defined once in Task 1's test file and reused. Constants `STATE_TO_CODE`, `CITATION_TO_CODE_NAME`, `CSV_FACTOR_TO_SLUG`, `REQUIRED_COLUMNS` named consistently across tasks.
