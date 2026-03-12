"""
Shared fixtures for Web Component source-analysis tests.

Copyright 2026 by GuidoGerb Publishing, LLC

Parses component JS files and extracts Shadow DOM templates
for structural and accessibility verification — no browser required.
"""

import re
from pathlib import Path

import pytest

COMPONENTS_DIR = Path(__file__).resolve().parent.parent / "frontend" / "components"


def _read_component(name: str) -> str:
    """Read a component JS source file."""
    return (COMPONENTS_DIR / f"{name}.js").read_text(encoding="utf-8")


def _extract_template(source: str) -> str:
    """Extract the first innerHTML template literal from component source."""
    match = re.search(r"\.innerHTML\s*=\s*`(.*?)`", source, re.DOTALL)
    return match.group(1) if match else ""


# ── app-root fixtures ──


@pytest.fixture
def app_root_source():
    return _read_component("app-root")


@pytest.fixture
def app_root_template(app_root_source):
    return _extract_template(app_root_source)


# ── app-header fixtures ──


@pytest.fixture
def app_header_source():
    return _read_component("app-header")


@pytest.fixture
def app_header_template(app_header_source):
    return _extract_template(app_header_source)


# ── app-3d-viewer fixtures ──


@pytest.fixture
def app_viewer_source():
    return _read_component("app-3d-viewer")


@pytest.fixture
def app_viewer_template(app_viewer_source):
    return _extract_template(app_viewer_source)
