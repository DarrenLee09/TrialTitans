# CSV Ingestion with Deduplication — Design

Status: Approved (verbal) 2026-05-09. Awaiting written-spec review before implementation.

## Goal

Load `data/eval-ca-vehicle-code.csv` into the SQLite `statutes` table, populate
`statute_factors` from the CSV's ground-truth `Contributing Factor` column, and
make the operation idempotent so re-running ingestion against the same CSV (or a
revised CSV that overlaps existing rows) produces no duplicates.

## Non-Goals

- Schema rewrites (Roadmap Phase 1 #4) — out of scope.
- Multi-state ingestion — only CA Vehicle Code is in the CSV.
- URL validation — handled separately by `harvester/validate_sources.py`.
- Replacing the keyword classifier — both ground-truth (CSV) and keyword-based
  (`harvester/classify_factors.py`) tagging will coexist; CSV is authoritative
  for the rows it covers.

## Inputs

- `data/eval-ca-vehicle-code.csv` — 41 rows, columns:
  `Statute, State, Universal Citation, Section #, Statute Language, Complete Statute, Contributing Factor`
- `data/source_registry.json` — used to construct `source_url` per section.
- The seeded `factors` table (8 rows) — preserved; the curated mapping below
  reuses these slugs where the CSV label matches the seed concept.

## Column & Value Mapping

| CSV column           | DB column        | Transform                                                                 |
|----------------------|------------------|---------------------------------------------------------------------------|
| `State`              | `jurisdiction`   | Normalize via `STATE_TO_CODE`: `"California" → "CA"`. Unknown → raise.    |
| `Universal Citation` | `code_name`      | Normalize via `CITATION_TO_CODE_NAME`: `"Cal. Veh. Code" → "Vehicle Code"`. Unknown → raise. |
| `Section #`          | `section`        | Verbatim (e.g., `"2800.1(a)"`).                                           |
| `Statute`            | `title`          | Full citation string serves as a human-readable title.                    |
| `Statute Language`   | `body`           | The actual statutory text. Required (NOT NULL in schema).                 |
| (computed)           | `source_url`     | Built from `source_registry.json` `query_template` using the section. If the registry has no entry for the (jurisdiction, code_name) pair, leave NULL — this is optional data and `validate_sources.py` already gracefully handles NULL `source_url`. |
| —                    | `effective_date` | Left NULL (CSV has no such column).                                       |

Both normalization dicts live at module level in `harvester/ingest_csv.py`.

## Deduplication Behavior

`statutes` schema has `UNIQUE (jurisdiction, code_name, section)`. Use
`INSERT OR IGNORE`. Track inserted vs skipped via `cursor.rowcount` per row.

This means the CSV is the source of truth on first ingestion, and subsequent
ingestions are no-ops for already-loaded sections. If a row's content needs to
change later, the operator must `DELETE` and re-run, or write a separate update
path. (This is the explicit user choice — the alternative was upsert.)

## Factor Ingestion (Approach A — Curated Mapping)

Module-level dict in `harvester/ingest_csv.py`:

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

Per row:

1. Resolve label → slug: dict hit, else `slugify(label)`.
2. `INSERT OR IGNORE INTO factors(slug, label, keywords)
   VALUES (?, ?, '[]')`. Idempotent — never overwrites a seeded factor's
   `keywords` (so `classify_factors` keeps working).
3. Look up `factors.id` by slug, then
   `INSERT OR IGNORE INTO statute_factors(statute_id, factor_id, confidence)
   VALUES (?, ?, 1.0)`.

`slugify`: lowercase, replace any run of non-`[a-z0-9]` with `_`, strip leading
and trailing `_`. Six-line inline helper, no new dependency.

Two CSV labels (`"Failure to Yield at a Yield Sign"` and
`"Failure to Yield the Right-of-Way"`) intentionally collapse to the same
`failure_to_yield` slug. If those need to be distinguished later, the dict is
the one place to change.

Unmapped CSV labels (≈9 of them — `"Improper Turning"`, `"Fleeing a Police Officer"`,
etc.) auto-create new factor rows with `slug = slugify(label)`,
`label = original CSV text`, `keywords = '[]'`.

## Public API

```python
def ingest(csv_path: Path = DEFAULT_CSV) -> dict:
    """Returns:
        {
          "inserted": int,            # statutes newly inserted
          "skipped": int,             # statutes whose key already existed
          "factors_created": int,     # new rows added to factors table
          "statute_factor_links": int # rows added to statute_factors
        }
    """
```

CLI (`__main__`) prints a human summary using these counts. Existing test
`test_eval_coverage.py::test_ingest_loads_all_rows` is updated to consume the
new dict shape, asserting `result["inserted"] + result["skipped"] >= 1`.

## Error Handling

Strict by default — we are loading legal data and silent skipping is the wrong
default.

- Missing required CSV column → raise `ValueError` listing the missing
  column(s) before any DB writes.
- Unknown `State` value → raise with the row number and offending value.
- Unknown `Universal Citation` value → same.
- Empty `Statute Language` → raise with row number (schema has `body NOT NULL`).
- Empty `Section #` → raise with row number.

Errors are raised before any partial commit. Callers can catch and surface.

## Testing (TDD — Tests Written First)

New file `tests/test_ingest_csv.py` covering:

1. **Column normalization**: `"California" → "CA"`,
   `"Cal. Veh. Code" → "Vehicle Code"` end up in the inserted row.
2. **Skip-on-conflict**: ingest the same CSV twice; second run reports
   `inserted=0, skipped=N`. Row count in `statutes` does not grow.
3. **Factor reuse**: a CSV row with `"DUI/DWI"` links to the seeded `dui`
   factor; no new `factors` row is created.
4. **Factor auto-create**: a CSV row with `"Improper Turning"` results in a
   new `factors` row with slug `improper_turning`.
5. **Slug collapse**: a CSV with both `"Failure to Yield at a Yield Sign"` and
   `"Failure to Yield the Right-of-Way"` rows links both statutes to the same
   `failure_to_yield` factor row (one factor row, two `statute_factors` rows).
6. **Required column missing**: ingest raises with a clear message; no rows
   inserted.
7. **Unknown jurisdiction**: ingest raises with row number and value.

Tests use the `_isolated_db` fixture from `tests/conftest.py`, write a small
fixture CSV via `tmp_path`, and call `ingest(tmp_csv)`.

`tests/test_eval_coverage.py` updated to consume the new return shape.

## Verification Before Claiming Done

1. `.venv/bin/python -m pytest -q` → all tests pass.
2. `.venv/bin/python -m harvester.ingest_csv` against the real eval CSV →
   prints `inserted=41, skipped=0, factors_created=N, statute_factor_links=41`
   on first run, then `inserted=0, skipped=41` on second run.
3. `.venv/bin/python -m harvester.build_fts_index` → reports 41 rows.
4. SQL spot-check: `SELECT COUNT(*) FROM statutes WHERE jurisdiction='CA'` → 41.
5. SQL spot-check:
   `SELECT f.slug, COUNT(*) FROM statute_factors sf JOIN factors f
    ON f.id = sf.factor_id GROUP BY f.slug ORDER BY 2 DESC` →
   matches the per-factor distribution in the source CSV.

## Implementation Surface

- `harvester/ingest_csv.py` — rewritten (existing 57-line file replaced).
- `tests/test_ingest_csv.py` — new.
- `tests/test_eval_coverage.py` — assertion shape updated.

No schema changes. No new dependencies. No changes to other harvester scripts,
retrieval modules, or the frontend.

## Risks

- **Curated mapping rot**: if the CSV grows new factor labels later, the
  `CSV_FACTOR_TO_SLUG` dict may need new entries to avoid auto-creating
  near-duplicates of seeded factors. Acceptable — small, reviewable surface.
- **Same-slug collapse loses distinction**: yield-sign vs yield-right-of-way
  are merged. Documented above; deliberate.
- **No update path**: skip-on-conflict means revised statute text in a future
  CSV won't propagate. This is the user's chosen tradeoff (vs upsert).
