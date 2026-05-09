"""Build and store vector embeddings for all statutes not yet embedded."""
from __future__ import annotations

import argparse
from typing import Any

import numpy as np
from tqdm import tqdm

from db.seed import connect

MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 64
_MODEL: Any | None = None


def _get_model() -> Any:
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer

        _MODEL = SentenceTransformer(MODEL_NAME)
    return _MODEL


def _rows_to_embed(rebuild: bool) -> list:
    sql = """
        SELECT s.id, s.title, s.body
        FROM statutes s
    """
    if not rebuild:
        sql += """
        LEFT JOIN statute_embeddings se ON se.statute_id = s.id
        WHERE se.statute_id IS NULL
        """
    sql += " ORDER BY s.id"
    with connect() as conn:
        return conn.execute(sql).fetchall()


def _text_for_embedding(row: dict) -> str:
    title = (row["title"] or "").strip()
    body = (row["body"] or "")[:1000].strip()
    return f"{title}\n{body}".strip()


def build_embeddings(rebuild: bool = False) -> int:
    rows = _rows_to_embed(rebuild=rebuild)
    if not rows:
        print("No statutes need embeddings.")
        return 0

    model = _get_model()
    processed = 0
    with connect() as conn:
        if rebuild:
            conn.execute("DELETE FROM statute_embeddings")
            conn.commit()
        for start in tqdm(range(0, len(rows), BATCH_SIZE), desc="Embedding statutes", unit="batch"):
            batch = rows[start : start + BATCH_SIZE]
            texts = [_text_for_embedding(row) for row in batch]
            vectors = model.encode(
                texts,
                batch_size=BATCH_SIZE,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            payload = [
                (
                    row["id"],
                    np.asarray(vector, dtype=np.float32).tobytes(),
                    MODEL_NAME,
                    int(np.asarray(vector).shape[0]),
                )
                for row, vector in zip(batch, vectors, strict=True)
            ]
            conn.executemany(
                """
                INSERT OR REPLACE INTO statute_embeddings(statute_id, embedding, model_name, dims)
                VALUES (?, ?, ?, ?)
                """,
                payload,
            )
            conn.commit()
            processed += len(batch)
    print(f"Stored {processed} embedding(s)")
    return processed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rebuild", action="store_true", help="Rebuild embeddings for all statutes")
    args = parser.parse_args()
    build_embeddings(rebuild=args.rebuild)


if __name__ == "__main__":
    main()
