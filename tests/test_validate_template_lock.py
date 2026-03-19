"""Tests for scripts/ui/validate_template_lock.py.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

from pathlib import Path

from scripts.ui.validate_template_lock import (
    _is_template_file,
    _move_files,
    _resolve_move_target,
    validate,
)


def test_ui_files_are_not_template_locked():
    assert _is_template_file("ui/src/main.js") is False
    assert _is_template_file("ui/scss/index.scss") is False


def test_api_files_are_not_template_locked():
    assert _is_template_file("api/README.md") is False
    assert _is_template_file("api/lambda/handler.py") is False


def test_root_files_are_template_locked():
    assert _is_template_file("run.py") is True
    assert _is_template_file("README.md") is True
    assert _is_template_file("requirements.txt") is True


def test_scripts_are_template_locked():
    assert _is_template_file("scripts/build_all.py") is True
    assert _is_template_file("scripts/ui/build.py") is True


def test_tests_are_template_locked():
    assert _is_template_file("tests/test_all.py") is True


def test_resources_are_template_locked():
    assert _is_template_file("resources/config/site.json") is True


def test_validate_no_changes_returns_empty(monkeypatch):
    """When git reports no changed files, validate passes."""
    monkeypatch.setattr(
        "scripts.ui.validate_template_lock._changed_files",
        lambda: [],
    )
    errors = validate()
    assert errors == []


def test_validate_only_user_dir_changes_returns_empty(monkeypatch):
    """Changes limited to api/ and ui/ always pass."""
    monkeypatch.setattr(
        "scripts.ui.validate_template_lock._changed_files",
        lambda: ["api/handler.py", "ui/src/main.js"],
    )
    errors = validate()
    assert errors == []


def test_validate_template_changes_returns_errors(monkeypatch):
    """Changes to template files produce errors when not forced and not interactive."""
    monkeypatch.setattr(
        "scripts.ui.validate_template_lock._changed_files",
        lambda: ["run.py", "scripts/build_all.py"],
    )
    monkeypatch.setattr("sys.stdin", type("FakeStdin", (), {"isatty": lambda self: False})())
    errors = validate(force=False)
    assert len(errors) == 2
    assert any("run.py" in e for e in errors)
    assert any("scripts/build_all.py" in e for e in errors)


def test_validate_force_allows_template_changes(monkeypatch):
    """--force bypasses the template lock."""
    monkeypatch.setattr(
        "scripts.ui.validate_template_lock._changed_files",
        lambda: ["run.py", "scripts/build_all.py"],
    )
    errors = validate(force=True)
    assert errors == []


def test_resolve_move_target_valid_ui():
    result = _resolve_move_target("ui/custom")
    assert result is not None
    assert result.name == "custom"
    assert "ui" in result.parts


def test_resolve_move_target_valid_api():
    result = _resolve_move_target("api/overrides")
    assert result is not None
    assert "api" in result.parts


def test_resolve_move_target_rejects_invalid():
    result = _resolve_move_target("scripts/hack")
    assert result is None


def test_resolve_move_target_rejects_root_path():
    result = _resolve_move_target("somewhere")
    assert result is None


def test_move_files_copies_and_preserves_structure(tmp_path, monkeypatch):
    """Files are copied into the target directory preserving their relative path."""
    monkeypatch.setattr("scripts.ui.validate_template_lock.ROOT", tmp_path)

    # Create a fake template file
    src = tmp_path / "scripts" / "build.py"
    src.parent.mkdir(parents=True)
    src.write_text("print('hello')\n", encoding="utf-8")

    # Stub git checkout to be a no-op
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: type("R", (), {"returncode": 0, "stderr": ""})(),
    )

    target = tmp_path / "ui" / "custom"
    errors = _move_files(["scripts/build.py"], target)
    assert errors == []
    assert (target / "scripts" / "build.py").exists()
    assert (target / "scripts" / "build.py").read_text(encoding="utf-8") == "print('hello')\n"


def test_move_files_warns_on_overwrite_non_interactive(tmp_path, monkeypatch):
    """In non-interactive mode, existing target files are overwritten with a warning."""
    monkeypatch.setattr("scripts.ui.validate_template_lock.ROOT", tmp_path)
    monkeypatch.setattr("sys.stdin", type("F", (), {"isatty": lambda self: False})())

    src = tmp_path / "run.py"
    src.write_text("new content\n", encoding="utf-8")

    target = tmp_path / "api" / "copy"
    dest = target / "run.py"
    dest.parent.mkdir(parents=True)
    dest.write_text("old content\n", encoding="utf-8")

    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: type("R", (), {"returncode": 0, "stderr": ""})(),
    )

    errors = _move_files(["run.py"], target)
    assert errors == []
    assert dest.read_text(encoding="utf-8") == "new content\n"


def test_validate_move_to_relocates_files(tmp_path, monkeypatch):
    """validate(move_to=...) copies locked files and returns no errors."""
    monkeypatch.setattr("scripts.ui.validate_template_lock.ROOT", tmp_path)

    src = tmp_path / "run.py"
    src.write_text("content\n", encoding="utf-8")

    monkeypatch.setattr(
        "scripts.ui.validate_template_lock._changed_files",
        lambda: ["run.py"],
    )
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: type("R", (), {"returncode": 0, "stderr": ""})(),
    )

    errors = validate(move_to="ui/custom")
    assert errors == []
    assert (tmp_path / "ui" / "custom" / "run.py").exists()


def test_validate_move_to_rejects_bad_target(monkeypatch):
    """move_to with a path outside api/ui returns an error."""
    monkeypatch.setattr(
        "scripts.ui.validate_template_lock._changed_files",
        lambda: ["run.py"],
    )
    errors = validate(move_to="scripts/hack")
    assert len(errors) == 1
    assert "api/ or ui/" in errors[0]


def test_is_template_file_bare_filename():
    """A bare filename (no slash) at repo root is template-locked."""
    assert _is_template_file("Makefile") is True
    assert _is_template_file(".gitignore") is True


def test_is_template_file_deeply_nested_user_dir():
    """Deep paths under api/ or ui/ are not template-locked."""
    assert _is_template_file("ui/src/components/deep/file.js") is False
    assert _is_template_file("api/v2/routes/users.py") is False


def test_resolve_move_target_normalises_backslashes():
    """Windows-style backslashes are normalised to forward slashes."""
    result = _resolve_move_target("ui\\overrides\\sub")
    assert result is not None
    assert "ui" in result.parts


def test_resolve_move_target_strips_trailing_slash():
    result = _resolve_move_target("api/overrides/")
    assert result is not None
    assert result.name == "overrides"


def test_resolve_move_target_nested_path():
    result = _resolve_move_target("ui/custom/deeply/nested")
    assert result is not None
    assert result.name == "nested"
    assert "ui" in result.parts


def test_move_files_skips_missing_source(tmp_path, monkeypatch):
    """If the source file doesn't exist, _move_files reports an error."""
    monkeypatch.setattr("scripts.ui.validate_template_lock.ROOT", tmp_path)

    target = tmp_path / "ui" / "custom"
    errors = _move_files(["nonexistent.py"], target)
    assert len(errors) == 1
    assert "source file not found" in errors[0]


def test_move_files_creates_nested_target_dirs(tmp_path, monkeypatch):
    """Target subdirectories are created automatically."""
    monkeypatch.setattr("scripts.ui.validate_template_lock.ROOT", tmp_path)

    src = tmp_path / "scripts" / "ui" / "build.py"
    src.parent.mkdir(parents=True)
    src.write_text("build\n", encoding="utf-8")

    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: type("R", (), {"returncode": 0, "stderr": ""})(),
    )

    target = tmp_path / "ui" / "custom"
    errors = _move_files(["scripts/ui/build.py"], target)
    assert errors == []
    dest = target / "scripts" / "ui" / "build.py"
    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == "build\n"


def test_move_files_reports_git_checkout_failure(tmp_path, monkeypatch):
    """If git checkout fails, the error is captured and returned."""
    monkeypatch.setattr("scripts.ui.validate_template_lock.ROOT", tmp_path)

    src = tmp_path / "run.py"
    src.write_text("content\n", encoding="utf-8")

    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: type("R", (), {"returncode": 1, "stderr": "error: pathspec"})(),
    )

    target = tmp_path / "ui" / "custom"
    errors = _move_files(["run.py"], target)
    assert len(errors) == 1
    assert "git checkout failed" in errors[0]


def test_move_files_multiple_files(tmp_path, monkeypatch):
    """Multiple template files are all copied to the target."""
    monkeypatch.setattr("scripts.ui.validate_template_lock.ROOT", tmp_path)

    for name in ("run.py", "README.md", "requirements.txt"):
        (tmp_path / name).write_text(f"{name} content\n", encoding="utf-8")

    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: type("R", (), {"returncode": 0, "stderr": ""})(),
    )

    target = tmp_path / "api" / "backup"
    errors = _move_files(["run.py", "README.md", "requirements.txt"], target)
    assert errors == []
    for name in ("run.py", "README.md", "requirements.txt"):
        assert (target / name).exists()


def test_move_files_overwrite_declined_interactive(tmp_path, monkeypatch):
    """In interactive mode, declining the overwrite prompt skips the file."""
    monkeypatch.setattr("scripts.ui.validate_template_lock.ROOT", tmp_path)
    monkeypatch.setattr("sys.stdin", type("TTY", (), {"isatty": lambda self: True})())
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")

    src = tmp_path / "run.py"
    src.write_text("new\n", encoding="utf-8")

    target = tmp_path / "ui" / "copy"
    dest = target / "run.py"
    dest.parent.mkdir(parents=True)
    dest.write_text("old\n", encoding="utf-8")

    # git checkout should not be called (nothing moved)
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: type("R", (), {"returncode": 0, "stderr": ""})(),
    )

    errors = _move_files(["run.py"], target)
    assert errors == []
    assert dest.read_text(encoding="utf-8") == "old\n"


def test_move_files_overwrite_accepted_interactive(tmp_path, monkeypatch):
    """In interactive mode, accepting overwrite replaces the file."""
    monkeypatch.setattr("scripts.ui.validate_template_lock.ROOT", tmp_path)
    monkeypatch.setattr("sys.stdin", type("TTY", (), {"isatty": lambda self: True})())
    monkeypatch.setattr("builtins.input", lambda _prompt: "y")

    src = tmp_path / "run.py"
    src.write_text("new\n", encoding="utf-8")

    target = tmp_path / "ui" / "copy"
    dest = target / "run.py"
    dest.parent.mkdir(parents=True)
    dest.write_text("old\n", encoding="utf-8")

    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: type("R", (), {"returncode": 0, "stderr": ""})(),
    )

    errors = _move_files(["run.py"], target)
    assert errors == []
    assert dest.read_text(encoding="utf-8") == "new\n"


def test_validate_mixed_user_and_template_changes(monkeypatch):
    """Only template-locked files are reported; user-dir changes pass through."""
    monkeypatch.setattr(
        "scripts.ui.validate_template_lock._changed_files",
        lambda: ["api/handler.py", "run.py", "ui/src/main.js", "scripts/build_all.py"],
    )
    monkeypatch.setattr("sys.stdin", type("F", (), {"isatty": lambda self: False})())
    errors = validate(force=False)
    assert len(errors) == 2
    paths_in_errors = " ".join(errors)
    assert "run.py" in paths_in_errors
    assert "scripts/build_all.py" in paths_in_errors
    assert "api/handler.py" not in paths_in_errors
    assert "ui/src/main.js" not in paths_in_errors


def test_validate_interactive_accept(monkeypatch):
    """Typing 'y' at the interactive prompt clears the error list."""
    monkeypatch.setattr(
        "scripts.ui.validate_template_lock._changed_files",
        lambda: ["run.py"],
    )
    monkeypatch.setattr("sys.stdin", type("TTY", (), {"isatty": lambda self: True})())
    monkeypatch.setattr("builtins.input", lambda _prompt: "y")
    errors = validate(force=False)
    assert errors == []


def test_validate_interactive_decline(monkeypatch):
    """Typing 'n' at the interactive prompt preserves errors."""
    monkeypatch.setattr(
        "scripts.ui.validate_template_lock._changed_files",
        lambda: ["run.py"],
    )
    monkeypatch.setattr("sys.stdin", type("TTY", (), {"isatty": lambda self: True})())
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")
    errors = validate(force=False)
    assert len(errors) == 1
    assert "run.py" in errors[0]


def test_validate_move_to_api_target(tmp_path, monkeypatch):
    """validate(move_to='api/...') works the same as ui/ targets."""
    monkeypatch.setattr("scripts.ui.validate_template_lock.ROOT", tmp_path)

    src = tmp_path / "run.py"
    src.write_text("content\n", encoding="utf-8")

    monkeypatch.setattr(
        "scripts.ui.validate_template_lock._changed_files",
        lambda: ["run.py"],
    )
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: type("R", (), {"returncode": 0, "stderr": ""})(),
    )

    errors = validate(move_to="api/overrides")
    assert errors == []
    assert (tmp_path / "api" / "overrides" / "run.py").exists()


def test_validate_force_takes_precedence_over_move_to(monkeypatch):
    """When both --force and --move-to are given, --force wins (no move)."""
    monkeypatch.setattr(
        "scripts.ui.validate_template_lock._changed_files",
        lambda: ["run.py"],
    )
    errors = validate(force=True, move_to="ui/custom")
    assert errors == []


def test_validate_error_messages_suggest_api_or_ui(monkeypatch):
    """Error messages guide the user to move changes into api/ or ui/."""
    monkeypatch.setattr(
        "scripts.ui.validate_template_lock._changed_files",
        lambda: ["run.py"],
    )
    monkeypatch.setattr("sys.stdin", type("F", (), {"isatty": lambda self: False})())
    errors = validate(force=False)
    assert all("api/ or ui/" in e for e in errors)
