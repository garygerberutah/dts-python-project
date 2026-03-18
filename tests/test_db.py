"""Tests for scripts/blockchain/db.py — PostgreSQL storage and SQL export.

Copyright 2026 by GuidoGerb Publishing, LLC

Verifies:
  - Table schema includes chain_content column
  - store_sbom inserts both sbom_content and chain_content
  - export_sbom_version_sql produces valid SQL INSERT statements
  - Docker fallback logic and connection helpers
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.blockchain.db import (
    ALTER_ADD_CHAIN_SQL,
    CREATE_TABLE_SQL,
    INSERT_SQL,
    SQL_EXPORT_DIR,
    export_sbom_version_sql,
)


# ---------------------------------------------------------------------------
# Schema tests (no DB connection required)
# ---------------------------------------------------------------------------


def test_create_table_includes_chain_content():
    """CREATE TABLE statement defines a chain_content JSONB column."""
    assert "chain_content" in CREATE_TABLE_SQL
    assert "JSONB" in CREATE_TABLE_SQL


def test_create_table_includes_sbom_content():
    """CREATE TABLE statement defines a sbom_content JSONB column."""
    assert "sbom_content" in CREATE_TABLE_SQL


def test_alter_adds_chain_column():
    """ALTER TABLE statement adds chain_content if missing."""
    assert "chain_content" in ALTER_ADD_CHAIN_SQL
    assert "ADD COLUMN IF NOT EXISTS" in ALTER_ADD_CHAIN_SQL


def test_insert_sql_includes_chain_content():
    """INSERT statement includes both sbom_content and chain_content."""
    assert "sbom_content" in INSERT_SQL
    assert "chain_content" in INSERT_SQL


def test_insert_sql_has_six_placeholders():
    """INSERT statement has exactly 6 parameter placeholders."""
    assert INSERT_SQL.count("%s") == 6


# ---------------------------------------------------------------------------
# store_sbom tests (mocked DB)
# ---------------------------------------------------------------------------


@patch("scripts.blockchain.db.connect")
@patch("scripts.blockchain.db._git_branch", return_value="dev")
@patch("scripts.blockchain.db._git_head_sha", return_value="a" * 40)
def test_store_sbom_passes_chain_data(mock_sha, mock_branch, mock_connect):
    """store_sbom sends chain_content to the INSERT statement."""
    from scripts.blockchain.db import store_sbom

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (42,)
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_connect.return_value = mock_conn

    manifest = {"version": "1.0", "file_count": 2, "files": []}
    chain_data = [{"index": 1, "proof": 100}]

    row_id = store_sbom(manifest, "abc123" + "0" * 58, chain_data=chain_data)

    assert row_id == 42
    # Verify the INSERT was called with 6 params including chain JSON
    call_args = mock_cursor.execute.call_args
    params = call_args[0][1]
    assert len(params) == 6
    # Last param is the chain JSON
    assert json.loads(params[5]) == chain_data


@patch("scripts.blockchain.db.connect")
@patch("scripts.blockchain.db._git_branch", return_value="main")
@patch("scripts.blockchain.db._git_head_sha", return_value="b" * 40)
def test_store_sbom_defaults_chain_to_empty_list(mock_sha, mock_branch, mock_connect):
    """store_sbom defaults chain_content to [] when not provided."""
    from scripts.blockchain.db import store_sbom

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (1,)
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_connect.return_value = mock_conn

    manifest = {"version": "1.0", "file_count": 0, "files": []}
    store_sbom(manifest, "0" * 64)

    call_args = mock_cursor.execute.call_args
    params = call_args[0][1]
    assert json.loads(params[5]) == []


# ---------------------------------------------------------------------------
# SQL export tests (mocked DB)
# ---------------------------------------------------------------------------


@patch("scripts.blockchain.db.connect")
def test_export_sbom_version_sql_creates_file(mock_connect, tmp_path):
    """export_sbom_version_sql writes a .sql file with INSERT statements."""
    from datetime import datetime, timezone

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        (
            1,
            "a" * 40,
            "dev",
            "c" * 64,
            10,
            {"version": "1.0"},
            [{"index": 1}],
            datetime(2026, 3, 18, 12, 0, 0, tzinfo=timezone.utc),
        ),
    ]
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_connect.return_value = mock_conn

    with patch("scripts.blockchain.db.SQL_EXPORT_DIR", tmp_path):
        sql_path = export_sbom_version_sql()

    assert sql_path.exists()
    assert sql_path.suffix == ".sql"
    content = sql_path.read_text(encoding="utf-8")
    assert "INSERT INTO public.sbom_version" in content
    assert "chain_content" in content
    assert "sbom_content" in content
    assert "Copyright 2026" in content


@patch("scripts.blockchain.db.connect")
def test_export_sql_escapes_single_quotes(mock_connect, tmp_path):
    """SQL export escapes single quotes in JSON content."""
    from datetime import datetime, timezone

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        (
            1,
            "a" * 40,
            "dev",
            "c" * 64,
            1,
            {"file": "it's here"},
            [],
            datetime(2026, 3, 18, 12, 0, 0, tzinfo=timezone.utc),
        ),
    ]
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_connect.return_value = mock_conn

    with patch("scripts.blockchain.db.SQL_EXPORT_DIR", tmp_path):
        sql_path = export_sbom_version_sql()

    content = sql_path.read_text(encoding="utf-8")
    # Single quotes in JSON values must be doubled for SQL
    assert "it''s here" in content


@patch("scripts.blockchain.db.connect")
def test_export_sql_empty_table(mock_connect, tmp_path):
    """SQL export handles an empty table gracefully."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_connect.return_value = mock_conn

    with patch("scripts.blockchain.db.SQL_EXPORT_DIR", tmp_path):
        sql_path = export_sbom_version_sql()

    content = sql_path.read_text(encoding="utf-8")
    assert "0 row(s)" in content
    assert "INSERT" not in content


# ---------------------------------------------------------------------------
# Docker Compose file existence
# ---------------------------------------------------------------------------


def test_docker_compose_exists():
    """Docker Compose file for project PostgreSQL exists."""
    compose_path = Path(__file__).resolve().parent.parent / "resources" / "postgres-data" / "docker-compose.yml"
    assert compose_path.exists(), f"Missing: {compose_path}"


def test_init_sql_exists():
    """Init SQL script for table creation exists."""
    init_path = (
        Path(__file__).resolve().parent.parent
        / "resources"
        / "postgres-data"
        / "init"
        / "001-create-tables.sql"
    )
    assert init_path.exists(), f"Missing: {init_path}"


def test_init_sql_matches_schema():
    """Init SQL contains the same schema as db.py CREATE_TABLE_SQL."""
    init_path = (
        Path(__file__).resolve().parent.parent
        / "resources"
        / "postgres-data"
        / "init"
        / "001-create-tables.sql"
    )
    content = init_path.read_text(encoding="utf-8")
    assert "chain_content" in content
    assert "sbom_content" in content
    assert "composite_sha256" in content
    assert "commit_sha" in content


# ---------------------------------------------------------------------------
# Connection fallback logic (mocked)
# ---------------------------------------------------------------------------


@patch("scripts.blockchain.db._try_connect")
def test_connect_tries_5432_first(mock_try):
    """connect() tries port 5432 before 5433."""
    from scripts.blockchain.db import connect

    mock_conn = MagicMock()
    mock_try.return_value = mock_conn

    result = connect()
    assert result is mock_conn
    mock_try.assert_called_once_with(5432)


@patch("scripts.blockchain.db._start_docker_db")
@patch("scripts.blockchain.db._try_connect")
def test_connect_falls_back_to_5433(mock_try, mock_start):
    """connect() falls back to port 5433 when 5432 is unavailable."""
    from scripts.blockchain.db import connect

    mock_conn = MagicMock()
    mock_try.side_effect = [None, mock_conn]

    result = connect()
    assert result is mock_conn
    assert mock_try.call_count == 2
    mock_try.assert_any_call(5432)
    mock_try.assert_any_call(5433)
    mock_start.assert_not_called()


@patch("scripts.blockchain.db._start_docker_db")
@patch("scripts.blockchain.db._try_connect")
def test_connect_starts_docker_when_both_fail(mock_try, mock_start):
    """connect() starts Docker when both 5432 and 5433 are unavailable."""
    from scripts.blockchain.db import connect

    mock_conn = MagicMock()
    # First two calls (5432, 5433) fail, third call (5433 after start) succeeds
    mock_try.side_effect = [None, None, mock_conn]

    result = connect()
    assert result is mock_conn
    mock_start.assert_called_once()
    assert mock_try.call_count == 3
