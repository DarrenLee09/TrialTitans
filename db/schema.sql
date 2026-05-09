-- TrialTitans / Legal Harvester schema (matches PRD section 3).

PRAGMA foreign_keys = ON;

-- 3.1 Jurisdictions ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS jurisdictions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT UNIQUE NOT NULL,        -- "CA", "TX", ...
    name            TEXT NOT NULL,               -- "California"
    statute_title   TEXT,                        -- "California Vehicle Code"
    base_url        TEXT,                        -- official legislature URL
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3.2 Statutes ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS statutes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    jurisdiction_id     INTEGER NOT NULL REFERENCES jurisdictions(id) ON DELETE CASCADE,
    citation            TEXT NOT NULL,           -- "CA Veh Code §23152"
    section_number      TEXT NOT NULL,           -- "23152"
    title               TEXT,
    full_text           TEXT NOT NULL CHECK (length(full_text) > 0),
    source_url          TEXT NOT NULL CHECK (length(source_url) > 0),
    scraped_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_verified         INTEGER NOT NULL DEFAULT 0,   -- 0/1 boolean
    UNIQUE (jurisdiction_id, section_number)
);

CREATE INDEX IF NOT EXISTS idx_statutes_jurisdiction
    ON statutes (jurisdiction_id, section_number);
CREATE INDEX IF NOT EXISTS idx_statutes_citation
    ON statutes (citation);

-- 3.3 Contributing factors ---------------------------------------------------
CREATE TABLE IF NOT EXISTS contributing_factors (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    code                TEXT UNIQUE NOT NULL,    -- "DUI", "FAILURE_TO_YIELD"
    label               TEXT NOT NULL,           -- "DUI", "Failure to Yield"
    description         TEXT,
    example_statutes    TEXT                     -- comma-separated example citations
);

-- 3.4 Statute ↔ factor join --------------------------------------------------
CREATE TABLE IF NOT EXISTS statute_factor_tags (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    statute_id      INTEGER NOT NULL REFERENCES statutes(id)             ON DELETE CASCADE,
    factor_id       INTEGER NOT NULL REFERENCES contributing_factors(id) ON DELETE CASCADE,
    confidence      REAL NOT NULL DEFAULT 1.0 CHECK (confidence BETWEEN 0 AND 1),
    tagged_by       TEXT NOT NULL DEFAULT 'manual',     -- 'claude' | 'manual'
    tagged_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (statute_id, factor_id)
);

CREATE INDEX IF NOT EXISTS idx_tags_factor   ON statute_factor_tags (factor_id);
CREATE INDEX IF NOT EXISTS idx_tags_statute  ON statute_factor_tags (statute_id);

-- 3.5 Sources registry -------------------------------------------------------
CREATE TABLE IF NOT EXISTS sources (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL,
    url                 TEXT NOT NULL,
    source_type         TEXT NOT NULL CHECK (source_type IN
        ('government','bar_association','court','plaintiff_firm','federal_agency')),
    jurisdiction_code   TEXT,                        -- "CA", "federal", or NULL
    reliability_score   INTEGER CHECK (reliability_score BETWEEN 1 AND 5),
    notes               TEXT
);

-- 3.6 Statute relationships --------------------------------------------------
CREATE TABLE IF NOT EXISTS statute_relationships (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    statute_id          INTEGER NOT NULL REFERENCES statutes(id) ON DELETE CASCADE,
    related_statute_id  INTEGER NOT NULL REFERENCES statutes(id) ON DELETE CASCADE,
    relationship_type   TEXT NOT NULL CHECK (relationship_type IN
        ('interprets','amends','references','case_law')),
    notes               TEXT,
    UNIQUE (statute_id, related_statute_id, relationship_type)
);

-- 3.7 FTS5 full-text index ---------------------------------------------------
CREATE VIRTUAL TABLE IF NOT EXISTS statute_fts USING fts5(
    citation,
    title,
    full_text,
    content='statutes',
    content_rowid='id'
);

-- Keep statute_fts in sync with statutes via triggers.
CREATE TRIGGER IF NOT EXISTS statutes_ai AFTER INSERT ON statutes BEGIN
    INSERT INTO statute_fts(rowid, citation, title, full_text)
    VALUES (new.id, new.citation, COALESCE(new.title, ''), new.full_text);
END;

CREATE TRIGGER IF NOT EXISTS statutes_ad AFTER DELETE ON statutes BEGIN
    INSERT INTO statute_fts(statute_fts, rowid, citation, title, full_text)
    VALUES ('delete', old.id, old.citation, COALESCE(old.title, ''), old.full_text);
END;

CREATE TRIGGER IF NOT EXISTS statutes_au AFTER UPDATE ON statutes BEGIN
    INSERT INTO statute_fts(statute_fts, rowid, citation, title, full_text)
    VALUES ('delete', old.id, old.citation, COALESCE(old.title, ''), old.full_text);
    INSERT INTO statute_fts(rowid, citation, title, full_text)
    VALUES (new.id, new.citation, COALESCE(new.title, ''), new.full_text);
END;

-- 3.8 Vector embeddings -------------------------------------------------------
CREATE TABLE IF NOT EXISTS statute_embeddings (
    statute_id  INTEGER PRIMARY KEY REFERENCES statutes(id) ON DELETE CASCADE,
    embedding   BLOB NOT NULL,
    model_name  TEXT NOT NULL DEFAULT 'all-MiniLM-L6-v2',
    dims        INTEGER NOT NULL DEFAULT 384,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);
