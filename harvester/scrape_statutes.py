"""Scrape statute bodies from official jurisdiction sites for any rows missing body text."""
from __future__ import annotations

import json
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from db.seed import connect

ROOT = Path(__file__).resolve().parent.parent
SOURCE_REGISTRY = ROOT / "data" / "source_registry.json"
USER_AGENT = "TrialTitans-Harvester/0.1 (research)"


def _registry() -> dict:
    return json.loads(SOURCE_REGISTRY.read_text())


def build_url(jurisdiction: str, code_name: str, section: str) -> str | None:
    reg = _registry().get(jurisdiction, {}).get(code_name)
    if not reg:
        return None
    return reg["base_url"] + reg["query_template"].format(section=section)


def fetch_body(url: str) -> str:
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    # Site-specific selectors live here; default to all text for now.
    return soup.get_text(separator="\n", strip=True)


def scrape_missing(delay_s: float = 1.0) -> int:
    updated = 0
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, jurisdiction, code_name, section FROM statutes WHERE body IS NULL OR body = ''"
        ).fetchall()
        for row in rows:
            url = build_url(row["jurisdiction"], row["code_name"], row["section"])
            if not url:
                continue
            try:
                body = fetch_body(url)
            except requests.RequestException as e:
                print(f"skip {row['section']}: {e}")
                continue
            conn.execute(
                "UPDATE statutes SET body = ?, source_url = ? WHERE id = ?",
                (body, url, row["id"]),
            )
            updated += 1
            time.sleep(delay_s)
        conn.commit()
    return updated


if __name__ == "__main__":
    n = scrape_missing()
    print(f"Updated {n} statutes")
