-- TrialTitans / Legal Statute Harvester schema

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS jurisdictions (
    code        TEXT PRIMARY KEY,          -- e.g. "CA", "NY"
    name        TEXT NOT NULL,
    country     TEXT NOT NULL DEFAULT 'US'
);

CREATE TABLE IF NOT EXISTS statutes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    jurisdiction    TEXT NOT NULL REFERENCES jurisdictions(code),
    code_name       TEXT NOT NULL,         -- e.g. "Vehicle Code"
    section         TEXT NOT NULL,         -- e.g. "22107"
    title           TEXT,
    body            TEXT NOT NULL,
    source_url      TEXT,
    effective_date  TEXT,
    fetched_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (jurisdiction, code_name, section)
);

CREATE INDEX IF NOT EXISTS idx_statutes_section
    ON statutes (jurisdiction, code_name, section);

CREATE TABLE IF NOT EXISTS factors (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    slug    TEXT UNIQUE NOT NULL,          -- e.g. "dui", "failure_to_yield"
    label   TEXT NOT NULL,
    keywords TEXT                          -- JSON array of trigger phrases
);

CREATE TABLE IF NOT EXISTS statute_factors (
    statute_id  INTEGER NOT NULL REFERENCES statutes(id) ON DELETE CASCADE,
    factor_id   INTEGER NOT NULL REFERENCES factors(id)  ON DELETE CASCADE,
    confidence  REAL DEFAULT 1.0,
    PRIMARY KEY (statute_id, factor_id)
);

CREATE TABLE IF NOT EXISTS statute_relationships (
    parent_id   INTEGER NOT NULL REFERENCES statutes(id) ON DELETE CASCADE,
    child_id    INTEGER NOT NULL REFERENCES statutes(id) ON DELETE CASCADE,
    rel_type    TEXT NOT NULL,             -- "amends", "references", "supersedes"
    PRIMARY KEY (parent_id, child_id, rel_type)
);

-- FTS5 virtual table for full-text search over statute body + title.
-- Populated by harvester.build_fts_index.
CREATE VIRTUAL TABLE IF NOT EXISTS statute_fts USING fts5(
    title,
    body,
    section UNINDEXED,
    jurisdiction UNINDEXED,
    content='statutes',
    content_rowid='id'
);
