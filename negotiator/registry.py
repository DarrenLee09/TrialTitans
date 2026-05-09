"""Load and query the holder registry from data/holder_registry.yaml."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

_REGISTRY_PATH = Path(__file__).parent.parent / "data" / "holder_registry.yaml"

# Keyword routing for fields whose outreach type depends on the closing_action text.
# Each entry maps a field name to a list of (keyword_list, registry_subkey) pairs.
# The first match wins.
_SUBTYPE_ROUTES: dict[str, list[tuple[list[str], str]]] = {
    "violation_evidence": [
        (
            ["phone", "wireless", "carrier", "text message", "cellular", "cell"],
            "violation_evidence.phone_records",
        ),
        (
            ["camera", "surveillance", "footage", "video", "cctv", "traffic camera"],
            "violation_evidence.camera_footage",
        ),
    ],
}


@lru_cache(maxsize=1)
def load_registry() -> dict:
    with open(_REGISTRY_PATH) as f:
        return yaml.safe_load(f)


def lookup(field: str, closing_action: str = "") -> dict | None:
    """
    Return the registry entry for a gap field, or None if not found.

    For fields listed in _SUBTYPE_ROUTES, keyword-matches closing_action to
    select the correct subtype entry before falling back to a direct field lookup.
    """
    registry = load_registry()
    fields = registry.get("fields", {})

    if field in _SUBTYPE_ROUTES:
        action_lower = closing_action.lower()
        for keywords, subtype_key in _SUBTYPE_ROUTES[field]:
            if any(kw in action_lower for kw in keywords):
                entry = fields.get(subtype_key)
                if entry is not None:
                    return entry

    return fields.get(field)
