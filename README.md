# TrialTitans — Legal Statute Harvester

Search and reason over jurisdictional statutes (starting with the California Vehicle Code) by citation, contributing factor, or natural-language accident description.

## Architecture

```
Frontend (Streamlit)
        │
        ▼
   App Layer
        │
        ▼
Retrieval Layer
  1. Exact SQL lookup (citation parser)
  2. SQLite FTS5 full-text search
  3. Keyword/rule-based factor matching
  4. Optional Claude reranking
        │
        ▼
SQLite DB  ──  statutes / statute_relationships / statute_fts
        │
        ▼
Ingestion Pipeline
  - CSV loader → scraper → URL validator → factor classifier → FTS index builder
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m db.seed                    # create db/legal_harvester.db
python -m harvester.ingest_csv       # load data/eval-ca-vehicle-code.csv
python -m harvester.build_fts_index  # build FTS5 index
streamlit run frontend/streamlit_app.py
```

## Layout

- `frontend/` — Streamlit UI
- `harvester/` — ingestion pipeline (CSV, scraping, classification, indexing)
- `retrieval/` — query routing, citation/exact/FTS/factor search, optional reranker
- `ai/` — Claude prompt templates and answer generation
- `db/` — SQLite schema + seed
- `data/` — source CSVs, jurisdiction registry
- `tests/` — pytest suites

## Environment

Set `ANTHROPIC_API_KEY` if you want AI reranking and natural-language answers.
