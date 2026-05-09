"""Semantic similarity search using stored statute embeddings."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from db.seed import connect

MODEL_NAME = "all-MiniLM-L6-v2"
_MODEL: Any | None = None
_CACHE: "EmbeddingCache | None" = None


@dataclass(slots=True)
class EmbeddingCache:
    signature: tuple[int, int, int, int]
    rows: list[dict]
    matrix: np.ndarray


def _db_signature() -> tuple[int, int, int, int]:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM statutes) AS statute_count,
                COALESCE((SELECT MAX(id) FROM statutes), 0) AS statute_max_id,
                (SELECT COUNT(*) FROM statute_embeddings) AS embedding_count,
                COALESCE((SELECT MAX(statute_id) FROM statute_embeddings), 0) AS embedding_max_id
            """
        ).fetchone()
    return tuple(row)


def _get_model() -> Any:
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer

        _MODEL = SentenceTransformer(MODEL_NAME)
    return _MODEL


def _build_snippet(body: str | None, limit: int = 320) -> str:
    text = " ".join((body or "").split())
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}…"


def invalidate_cache() -> None:
    global _CACHE
    _CACHE = None


def _load_cache() -> EmbeddingCache:
    global _CACHE
    signature = _db_signature()
    if _CACHE is not None and _CACHE.signature == signature:
        return _CACHE

    rows: list[dict] = []
    vectors: list[np.ndarray] = []
    with connect() as conn:
        db_rows = conn.execute(
            """
            SELECT
                s.id,
                j.code           AS jurisdiction,
                j.statute_title  AS code_name,
                s.section_number AS section,
                s.title,
                s.full_text      AS body,
                s.citation,
                s.source_url,
                se.embedding,
                se.dims
            FROM statute_embeddings se
            JOIN statutes s      ON s.id = se.statute_id
            JOIN jurisdictions j ON j.id = s.jurisdiction_id
            ORDER BY s.id
            """
        ).fetchall()

    for row in db_rows:
        vector = np.frombuffer(row["embedding"], dtype=np.float32)
        dims = int(row["dims"] or 0)
        if dims and vector.size != dims:
            continue
        vectors.append(vector)
        rows.append(
            {
                "id": row["id"],
                "jurisdiction": row["jurisdiction"],
                "code_name": row["code_name"],
                "section": row["section"],
                "title": row["title"],
                "body": row["body"],
                "citation": row["citation"],
                "source_url": row["source_url"],
                "snippet": _build_snippet(row["body"]),
            }
        )

    matrix = np.vstack(vectors).astype(np.float32, copy=False) if vectors else np.empty((0, 0), dtype=np.float32)
    _CACHE = EmbeddingCache(signature=signature, rows=rows, matrix=matrix)
    return _CACHE


def has_embeddings(jurisdiction: str | None = None) -> bool:
    sql = """
        SELECT 1
        FROM statute_embeddings se
        JOIN statutes s      ON s.id = se.statute_id
        JOIN jurisdictions j ON j.id = s.jurisdiction_id
    """
    args: list[str] = []
    if jurisdiction:
        sql += " WHERE j.code = ?"
        args.append(jurisdiction)
    sql += " LIMIT 1"
    with connect() as conn:
        return conn.execute(sql, args).fetchone() is not None


def search(query: str, jurisdiction: str | None = None, limit: int = 20) -> list[dict]:
    cache = _load_cache()
    if not cache.rows or cache.matrix.size == 0:
        return []

    indices = [i for i, row in enumerate(cache.rows) if not jurisdiction or row["jurisdiction"] == jurisdiction]
    if not indices:
        return []

    model = _get_model()
    query_vector = np.asarray(
        model.encode(query, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False),
        dtype=np.float32,
    )
    matrix = cache.matrix[indices]
    similarities = matrix @ query_vector
    top_positions = np.argsort(similarities)[::-1][:limit]

    results: list[dict] = []
    for position in top_positions:
        index = indices[int(position)]
        result = dict(cache.rows[index])
        score = float(similarities[int(position)])
        result["score"] = max(0.0, min(1.0, (score + 1.0) / 2.0))
        results.append(result)
    return results
