"""Tests for scripts/blockchain/sync_db.py — rebuild PG from chain.json.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import scripts.blockchain.sync_db as sync_mod
from scripts.blockchain.sync_db import sync


def test_sync_inserts_sbom_entries(tmp_path):
    """sync() inserts SBOM hashes from chain.json into PostgreSQL."""
    chain_data = [
        {
            "index": 1,
            "timestamp": 1000,
            "sbom_hashes": [],
            "proof": 100,
            "previous_hash": "1",
        },
        {
            "index": 2,
            "timestamp": 2000,
            "sbom_hashes": [{"repo": "ggp3d", "bom_hash": "abc123"}],
            "proof": 200,
            "previous_hash": "fakehash",
        },
    ]
    chain_file = tmp_path / "chain.json"
    chain_file.write_text(json.dumps(chain_data), encoding="utf-8")

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    with (
        patch.object(sync_mod, "get_connection", return_value=mock_conn),
        patch.object(sync_mod, "ensure_table"),
        patch("scripts.blockchain.sync_db.Blockchain") as mock_bc_cls,
    ):
        mock_bc = MagicMock()
        mock_bc.verify_chain.return_value = True
        mock_bc.chain = chain_data
        mock_bc_cls.load.return_value = mock_bc

        count = sync(chain_file)
        assert count == 1
        mock_cursor.execute.assert_called_once()


def test_sync_fails_on_bad_chain(tmp_path):
    """sync() raises RuntimeError when blockchain verification fails."""
    chain_file = tmp_path / "chain.json"
    chain_file.write_text("[]", encoding="utf-8")

    with patch("scripts.blockchain.sync_db.Blockchain") as mock_bc_cls:
        mock_bc = MagicMock()
        mock_bc.verify_chain.return_value = False
        mock_bc_cls.load.return_value = mock_bc

        try:
            sync(chain_file)
            assert False, "Expected RuntimeError"
        except RuntimeError:
            pass


def test_main_returns_zero_on_success():
    """main() returns 0 when sync succeeds."""
    with patch.object(sync_mod, "sync", return_value=5):
        assert sync_mod.main() == 0


def test_main_returns_one_on_connection_failure():
    """main() returns 1 when PG is unreachable."""
    import psycopg2

    with patch.object(
        sync_mod, "sync",
        side_effect=psycopg2.OperationalError("fail"),
    ):
        assert sync_mod.main() == 1
