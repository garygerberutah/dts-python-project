"""Tests for scripts/ui/build.py — WASM compilation, template rendering, asset copy.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import scripts.ui.build as build_mod
from scripts.ui.build import (
    _load_site_config,
    _resolve_env_vars,
    _run,
    build_wasm,
    copy_assets,
    render_templates,
)


def test_load_site_config():
    """_load_site_config returns a dict with expected keys."""
    config = _load_site_config()
    assert isinstance(config, dict)
    assert "project_name" in config
    assert "wasm_module" in config
    assert "lang" in config


def test_resolve_env_vars_replaces_markers():
    """_resolve_env_vars replaces ${KEY} patterns."""
    text = "Hello ${NAME}, version ${VERSION}"
    result = _resolve_env_vars(text, {"NAME": "World", "VERSION": "1.0"})
    assert result == "Hello World, version 1.0"


def test_resolve_env_vars_no_markers():
    """_resolve_env_vars returns text unchanged when no markers exist."""
    text = "No markers here"
    result = _resolve_env_vars(text, {"KEY": "val"})
    assert result == "No markers here"


def test_resolve_env_vars_empty_replacements():
    """_resolve_env_vars leaves markers when key not in replacements."""
    text = "Hello ${MISSING}"
    result = _resolve_env_vars(text, {})
    assert result == "Hello ${MISSING}"


def test_render_templates_creates_index_html(tmp_path):
    """render_templates produces dist/index.html from templates."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    base_tmpl = templates_dir / "base.html.j2"
    base_tmpl.write_text(
        '<!DOCTYPE html><html lang="{{ lang }}">'
        "<head><title>{% block title %}{% endblock %}</title></head>"
        "<body>{% block body %}{% endblock %}</body></html>",
        encoding="utf-8",
    )

    index_tmpl = templates_dir / "index.html.j2"
    index_tmpl.write_text(
        '{% extends "base.html.j2" %}'
        "{% block title %}{{ app_title }}{% endblock %}"
        "{% block body %}<main>{{ app_description }}</main>{% endblock %}",
        encoding="utf-8",
    )

    dist = tmp_path / "dist"
    dist.mkdir()

    site_json = tmp_path / "site.json"
    site_json.write_text(
        json.dumps(
            {
                "project_name": "TestApp",
                "project_description": "Test Description",
                "lang": "en",
                "repository": {"url": ""},
            }
        ),
        encoding="utf-8",
    )

    with (
        patch.object(build_mod, "TEMPLATES_DIR", templates_dir),
        patch.object(build_mod, "DIST_DIR", dist),
        patch.object(build_mod, "SITE_JSON", site_json),
        patch.object(build_mod, "ROOT", tmp_path),
    ):
        render_templates(favicon_filename="favicon.svg")

    html = (dist / "index.html").read_text(encoding="utf-8")
    assert "TestApp" in html
    assert 'lang="en"' in html


def test_copy_assets_copies_main_js(tmp_path):
    """copy_assets copies main.js to dist/js/."""
    ui_dir = tmp_path / "ui"
    src = ui_dir / "src"
    (src / "components").mkdir(parents=True)
    (src / "components" / "app-root.js").write_text(
        "/** Copyright 2026 by GuidoGerb Publishing, LLC */\nexport {}",
        encoding="utf-8",
    )
    main_js = src / "main.js"
    main_js.write_text(
        '/** Copyright 2026 by GuidoGerb Publishing, LLC */\nconsole.info("ok");',
        encoding="utf-8",
    )

    scss_dir = ui_dir / "scss"
    scss_dir.mkdir(parents=True)
    (scss_dir / "index.scss").write_text(
        "/* Copyright 2026 by GuidoGerb Publishing, LLC */", encoding="utf-8"
    )

    dist = tmp_path / "dist"
    dist.mkdir()

    site_json = tmp_path / "site.json"
    site_json.write_text(
        json.dumps(
            {
                "project_name": "Test",
                "repository": {"url": ""},
                "wasm_module": "test_wasm",
            }
        ),
        encoding="utf-8",
    )

    with (
        patch.object(build_mod, "UI_DIR", ui_dir),
        patch.object(build_mod, "DIST_DIR", dist),
        patch.object(build_mod, "ROOT", tmp_path),
        patch.object(build_mod, "SITE_JSON", site_json),
    ):
        favicon_name = copy_assets()

    assert (dist / "js" / "main.js").exists()
    assert (dist / "components" / "app-root.js").exists()
    assert "favicon-" in favicon_name
    assert favicon_name.endswith(".svg")


def test_main_returns_zero_on_success():
    """main() returns 0 when build succeeds."""
    with patch.object(build_mod, "build") as mock_build:
        mock_build.return_value = None
        result = build_mod.main()
        assert result == 0


def test_main_returns_one_on_failure():
    """main() returns 1 when build raises."""
    with patch.object(build_mod, "build", side_effect=RuntimeError("fail")):
        result = build_mod.main()
        assert result == 1


# --- _run tests ---


def test_run_success():
    """_run completes without error for a valid command."""
    _run(["echo", "hello"])


def test_run_missing_executable():
    """_run raises RuntimeError when executable is not found."""
    with pytest.raises(RuntimeError, match="not found"):
        _run(["__nonexistent_binary__"])


def test_run_nonzero_exit():
    """_run raises RuntimeError on nonzero exit code."""
    with pytest.raises(RuntimeError, match="Command failed"):
        _run(["false"])


# --- build_wasm tests ---


def test_build_wasm_copies_pkg(tmp_path):
    """build_wasm calls wasm-pack and copies pkg to dist/wasm."""
    wasm_dir = tmp_path / "wasm"
    wasm_dir.mkdir()
    pkg_dir = wasm_dir / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "test.wasm").write_bytes(b"\x00wasm")

    dist = tmp_path / "dist"
    dist.mkdir()

    with (
        patch.object(build_mod, "WASM_DIR", wasm_dir),
        patch.object(build_mod, "DIST_DIR", dist),
        patch.object(build_mod, "_run") as mock_run,
    ):
        build_wasm()

    mock_run.assert_called_once()
    assert (dist / "wasm" / "test.wasm").exists()


# --- copy_assets with favicon_src existing ---


def test_copy_assets_with_existing_favicon(tmp_path):
    """copy_assets copies a real favicon file when assets/favicon.svg exists."""
    ui_dir = tmp_path / "ui"
    src = ui_dir / "src"
    (src / "components").mkdir(parents=True)
    (src / "components" / "app-root.js").write_text(
        "/** Copyright 2026 by GuidoGerb Publishing, LLC */\nexport {}",
        encoding="utf-8",
    )
    main_js = src / "main.js"
    main_js.write_text(
        '/** Copyright 2026 by GuidoGerb Publishing, LLC */\nconsole.info("ok");',
        encoding="utf-8",
    )

    scss_dir = ui_dir / "scss"
    scss_dir.mkdir(parents=True)
    (scss_dir / "index.scss").write_text(
        "/* Copyright 2026 by GuidoGerb Publishing, LLC */", encoding="utf-8"
    )

    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    (assets_dir / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><circle r="1"/></svg>',
        encoding="utf-8",
    )

    dist = tmp_path / "dist"
    dist.mkdir()

    site_json = tmp_path / "site.json"
    site_json.write_text(
        json.dumps(
            {
                "project_name": "Test",
                "repository": {"url": ""},
                "wasm_module": "test_wasm",
            }
        ),
        encoding="utf-8",
    )

    with (
        patch.object(build_mod, "UI_DIR", ui_dir),
        patch.object(build_mod, "DIST_DIR", dist),
        patch.object(build_mod, "ROOT", tmp_path),
        patch.object(build_mod, "SITE_JSON", site_json),
    ):
        favicon_name = copy_assets()

    assert "favicon-" in favicon_name


def test_copy_assets_resolves_env_vars(tmp_path):
    """copy_assets replaces ${PROJECT_NAME} markers in JS files."""
    ui_dir = tmp_path / "ui"
    src = ui_dir / "src"
    (src / "components").mkdir(parents=True)
    (src / "components" / "app.js").write_text(
        '/** Copyright 2026 by GuidoGerb Publishing, LLC */\nconst name = "${PROJECT_NAME}";',
        encoding="utf-8",
    )

    scss_dir = ui_dir / "scss"
    scss_dir.mkdir(parents=True)
    (scss_dir / "index.scss").write_text(
        "/* Copyright 2026 by GuidoGerb Publishing, LLC */", encoding="utf-8"
    )

    dist = tmp_path / "dist"
    dist.mkdir()

    site_json = tmp_path / "site.json"
    site_json.write_text(
        json.dumps(
            {
                "project_name": "MyApp",
                "repository": {"url": "https://example.com"},
                "wasm_module": "my_wasm",
            }
        ),
        encoding="utf-8",
    )

    with (
        patch.object(build_mod, "UI_DIR", ui_dir),
        patch.object(build_mod, "DIST_DIR", dist),
        patch.object(build_mod, "ROOT", tmp_path),
        patch.object(build_mod, "SITE_JSON", site_json),
    ):
        copy_assets()

    content = (dist / "components" / "app.js").read_text(encoding="utf-8")
    assert "MyApp" in content
    assert "${PROJECT_NAME}" not in content
