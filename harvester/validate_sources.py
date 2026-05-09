"""Sanity-check that source_url for each statute returns 200."""
from __future__ import annotations

import requests

from db.seed import connect

USER_AGENT = "TrialTitans-Validator/0.1"


def validate() -> tuple[int, list[tuple[int, str, int]]]:
    failures: list[tuple[int, str, int]] = []
    ok = 0
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, source_url FROM statutes WHERE source_url IS NOT NULL AND source_url != ''"
        ).fetchall()
        for row in rows:
            try:
                r = requests.head(
                    row["source_url"],
                    headers={"User-Agent": USER_AGENT},
                    timeout=10,
                    allow_redirects=True,
                )
                if r.status_code == 200:
                    ok += 1
                else:
                    failures.append((row["id"], row["source_url"], r.status_code))
            except requests.RequestException:
                failures.append((row["id"], row["source_url"], -1))
    return ok, failures


if __name__ == "__main__":
    ok, failures = validate()
    print(f"OK: {ok}    Failures: {len(failures)}")
    for sid, url, code in failures[:20]:
        print(f"  [{code}] statute {sid}  {url}")
