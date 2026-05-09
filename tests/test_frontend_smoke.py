"""Smoke tests: every frontend module imports and exposes its render entrypoint."""
from __future__ import annotations

import importlib

import pytest


@pytest.mark.parametrize(
    "module_name, attr",
    [
        ("frontend.styles", "inject"),
        ("frontend.components.top_bar", "render"),
        ("frontend.components.hero_search", "render"),
        ("frontend.components.empty_state", "render"),
        ("frontend.components.loading_state", "render"),
        ("frontend.components.result_card", "render"),
        ("frontend.components.case_file_sidebar", "render"),
        ("frontend.components.ai_memo_rail", "render"),
    ],
)
def test_module_exposes_callable(module_name: str, attr: str) -> None:
    mod = importlib.import_module(module_name)
    assert callable(getattr(mod, attr)), f"{module_name}.{attr} should be callable"


def test_streamlit_app_imports() -> None:
    """The entrypoint script should import without raising."""
    importlib.import_module("frontend.streamlit_app")


def test_old_components_removed() -> None:
    """The replaced components should no longer be importable."""
    for old in ("frontend.components.search_bar", "frontend.components.case_workspace"):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(old)
