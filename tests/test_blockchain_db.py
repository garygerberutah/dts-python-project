"""Tests for scripts/blockchain/db.py — PostgreSQL SBOM storage.

Copyright 2026 by GuidoGerb Publishing, LLC

The actual PostgreSQL database is not available in CI/test environments,
so these tests verify the module's helper functions and SQL constants.
Connection-dependent functions are tested with mocks.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import scripts.blockchain.db as db_mod
from scripts.blockchain.db import (
    CREATE_TABLE_SQL,
    INSERT_SQL,
    _git_branch,
    _git_head_sha,
    _pg_host,
    _try_connect,
    ensure_table,
    get_connection,
    main,
    store_sbom,
)


def test_create_table_sql_contains_table_name():
    """CREATE_TABLE_SQL references the sbom_version table."""
    assert "sbom_version" in CREATE_TABLE_SQL
    assert "CREATE TABLE IF NOT EXISTS" in CREATE_TABLE_SQL


def test_create_table_sql_has_expected_columns():
    """The SQL DDL includes all expected columns."""
    for col in ("commit_sha", "branch", "composite_sha256", "file_count", "sbom_content"):
        assert col in CREATE_TABLE_SQL


def test_insert_sql_has_placeholders():
    """INSERT_SQL contains parameter placeholders."""
    assert "%s" in INSERT_SQL
    assert "RETURNING id" in INSERT_SQL


def test_git_head_sha_returns_40_chars():
    """_git_head_sha returns a valid hex SHA or 40 zeros."""
    sha = _git_head_sha()
    assert len(sha) == 40


def test_git_branch_returns_string():
    """_git_branch returns a non-empty branch name."""
    branch = _git_branch()
    assert isinstance(branch, str)
    assert len(branch) > 0


def test_pg_host_returns_localhost_or_ip():
    """_pg_host returns 'localhost' or a valid IPv4 address."""
    host = _pg_host()
    assert host == "localhost" or host.count(".") == 3


@patch("scripts.blockchain.db.get_connection")
def test_ensure_table_calls_execute(mock_get_conn):
    """ensure_table connects and executes the CREATE TABLE SQL."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_get_conn.return_value = mock_conn

    ensure_table()

    mock_get_conn.assert_called_once()
    mock_cursor.execute.assert_called_once_with(CREATE_TABLE_SQL)
    mock_conn.close.assert_called_once()


@patch("scripts.blockchain.db.get_connection")
def test_store_sbom_inserts_and_returns_id(mock_get_conn):
    """store_sbom inserts a row and returns the new id."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (42,)
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_get_conn.return_value = mock_conn

    manifest = {"version": "1.0", "file_count": 5, "files": []}
    row_id = store_sbom(manifest, "abc123" * 10 + "abcd")

    assert row_id == 42
    mock_cursor.execute.assert_called_once()
    mock_conn.close.assert_called_once()


@patch("scripts.blockchain.db.get_connection")
def test_main_returns_zero_on_success(mock_get_conn):
    """main() returns 0 when ensure_table succeeds."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_get_conn.return_value = mock_conn

    assert main() == 0


def test_main_returns_one_on_connection_failure():
    """main() returns 1 when PostgreSQL is unreachable."""
    import psycopg2

    with patch.object(
        db_mod,
        "get_connection",
        side_effect=psycopg2.OperationalError("connection refused"),
    ):
        assert main() == 1


def test_pg_host_wsl2_returns_gateway_ip():
    """_pg_host returns the gateway IP inside WSL2."""
    with (
        patch("scripts.blockchain.db.platform") as mock_platform,
        patch("scripts.blockchain.db.Path") as mock_path_cls,
        patch("scripts.blockchain.db.subprocess") as mock_subprocess,
    ):
        mock_platform.system.return_value = "Linux"
        mock_path_cls.return_value.exists.return_value = True
        mock_result = MagicMock()
        mock_result.stdout = "default via 172.28.0.1 dev eth0"
        mock_subprocess.run.return_value = mock_result
        host = _pg_host()
        assert host == "172.28.0.1"


def test_git_head_sha_failure_returns_zeros():
    """_git_head_sha returns 40 zeros when git fails."""
    with patch("scripts.blockchain.db.subprocess") as mock_subprocess:
        mock_result = MagicMock()
        mock_result.returncode = 128
        mock_result.stdout = ""
        mock_subprocess.run.return_value = mock_result
        sha = _git_head_sha()
        assert sha == "0" * 40


def test_git_branch_failure_returns_unknown():
    """_git_branch returns 'unknown' when git fails."""
    with patch("scripts.blockchain.db.subprocess") as mock_subprocess:
        mock_result = MagicMock()
        mock_result.returncode = 128
        mock_result.stdout = ""
        mock_subprocess.run.return_value = mock_result
        branch = _git_branch()
        assert branch == "unknown"


# --- Connection fallback tests ---


def test_try_connect_returns_conn_on_success():
    """_try_connect returns a connection object on success."""
    mock_conn = MagicMock()
    with patch("scripts.blockchain.db.psycopg2") as mock_pg:
        mock_pg.connect.return_value = mock_conn
        result = _try_connect("localhost", 5432)
        assert result is mock_conn


def test_try_connect_returns_none_on_failure():
    """_try_connect returns None when connection fails."""
    import psycopg2

    with patch("scripts.blockchain.db.psycopg2") as mock_pg:
        mock_pg.OperationalError = psycopg2.OperationalError
        mock_pg.connect.side_effect = psycopg2.OperationalError("fail")
        result = _try_connect("localhost", 5432)
        assert result is None


def test_get_connection_prefers_localhost():
    """get_connection returns the localhost connection first."""
    mock_conn = MagicMock()
    with patch.object(db_mod, "_try_connect") as mock_try:
        mock_try.return_value = mock_conn
        conn = get_connection()
        assert conn is mock_conn
        # First call should be to localhost
        first_call = mock_try.call_args_list[0]
        assert first_call[0][1] == db_mod._LOCALHOST_PORT


def test_get_connection_falls_back_to_docker():
    """get_connection tries Docker port when localhost fails."""
    mock_conn = MagicMock()

    def side_effect(host, port):
        if port == db_mod._DOCKER_PORT:
            return mock_conn
        return None

    with patch.object(db_mod, "_try_connect", side_effect=side_effect):
        conn = get_connection()
        assert conn is mock_conn


def test_get_connection_starts_docker_on_full_failure():
    """get_connection starts Docker when both ports are initially unreachable."""
    mock_conn = MagicMock()
    call_count = 0

    def side_effect(host, port):
        nonlocal call_count
        call_count += 1
        # Third call to Docker port succeeds (after _ensure_docker_pg)
        if call_count >= 3 and port == db_mod._DOCKER_PORT:
            return mock_conn
        return None

    with (
        patch.object(db_mod, "_try_connect", side_effect=side_effect),
        patch.object(db_mod, "_ensure_docker_pg", return_value=True),
    ):
        conn = get_connection()
        assert conn is mock_conn


def test_get_connection_raises_when_all_fail():
    """get_connection raises OperationalError when nothing works."""
    import psycopg2

    with (
        patch.object(db_mod, "_try_connect", return_value=None),
        patch.object(db_mod, "_ensure_docker_pg", return_value=False),
    ):
        try:
            get_connection()
            assert False, "Expected OperationalError"
        except psycopg2.OperationalError:
            pass


def test_ensure_docker_pg_no_docker():
    """_ensure_docker_pg returns False when docker is not installed."""
    with patch("scripts.blockchain.db.shutil") as mock_shutil:
        mock_shutil.which.return_value = None
        assert db_mod._ensure_docker_pg() is False


def test_ensure_docker_pg_already_running():
    """_ensure_docker_pg returns True when container is already running."""
    with (
        patch("scripts.blockchain.db.shutil") as mock_shutil,
        patch("scripts.blockchain.db.subprocess") as mock_sub,
    ):
        mock_shutil.which.return_value = "/usr/bin/docker"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "true\n"
        mock_sub.run.return_value = mock_result
        assert db_mod._ensure_docker_pg() is True
