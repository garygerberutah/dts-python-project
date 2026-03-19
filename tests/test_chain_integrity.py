"""Tests for blockchain chain integrity and git-history protection.

Copyright 2026 by DTS, The State of Utah

Verifies:
  - Blockchain hash-chain verification detects tampered blocks
  - commit_sha is recorded in sbom_hash entries
  - verify_commit_ancestry detects rewritten git history
  - verify_index_worktree catches unstaged working-tree changes
  - verify_chain_db_consistency cross-references chain vs database
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.blockchain.sbom import Blockchain


# ---------------------------------------------------------------------------
# Blockchain hash-chain verification
# ---------------------------------------------------------------------------


def test_verify_chain_valid():
    """A freshly-built chain with two mined blocks passes verification."""
    bc = Blockchain()
    bc.add_sbom_hash("repo", "a" * 64, commit_sha="b" * 40)
    proof = bc.proof_of_work()
    bc.new_block(proof=proof)
    assert bc.verify_chain() is True


def test_verify_chain_detects_tampered_block():
    """Modifying a block's content invalidates the chain."""
    bc = Blockchain()
    bc.add_sbom_hash("repo", "a" * 64)
    proof = bc.proof_of_work()
    bc.new_block(proof=proof)

    # Tamper with the genesis block
    bc.chain[0]["proof"] = 999999
    assert bc.verify_chain() is False


# ---------------------------------------------------------------------------
# commit_sha in sbom_hash entries
# ---------------------------------------------------------------------------


def test_add_sbom_hash_stores_commit_sha():
    """add_sbom_hash records commit_sha in the pending entry."""
    bc = Blockchain()
    bc.add_sbom_hash("repo", "a" * 64, commit_sha="c" * 40)
    assert len(bc.pending_sbom_hashes) == 1
    assert bc.pending_sbom_hashes[0]["commit_sha"] == "c" * 40


def test_add_sbom_hash_omits_commit_sha_when_empty():
    """add_sbom_hash without commit_sha omits the key (legacy compat)."""
    bc = Blockchain()
    bc.add_sbom_hash("repo", "a" * 64)
    assert "commit_sha" not in bc.pending_sbom_hashes[0]


def test_commit_sha_persists_in_mined_block():
    """commit_sha survives from pending entry into the mined block."""
    bc = Blockchain()
    sha = "d" * 40
    bc.add_sbom_hash("repo", "a" * 64, commit_sha=sha)
    proof = bc.proof_of_work()
    bc.new_block(proof=proof)

    block = bc.chain[-1]
    assert block["sbom_hashes"][0]["commit_sha"] == sha


def test_commit_sha_survives_save_load(tmp_path):
    """commit_sha round-trips through save/load."""
    chain_file = tmp_path / "chain.json"
    sha = "e" * 40

    bc = Blockchain()
    bc.add_sbom_hash("repo", "a" * 64, commit_sha=sha)
    proof = bc.proof_of_work()
    bc.new_block(proof=proof)
    bc.save(chain_file)

    loaded = Blockchain.load(chain_file)
    entry = loaded.chain[-1]["sbom_hashes"][0]
    assert entry["commit_sha"] == sha


# ---------------------------------------------------------------------------
# verify_commit_ancestry
# ---------------------------------------------------------------------------


@patch("scripts.blockchain.sbom.subprocess.run")
def test_verify_ancestry_valid(mock_run):
    """verify_commit_ancestry passes when commits are in ancestral order."""
    mock_run.return_value = MagicMock(returncode=0)

    bc = Blockchain()
    bc.add_sbom_hash("repo", "a" * 64, commit_sha="a" * 40)
    bc.new_block(proof=bc.proof_of_work())
    bc.add_sbom_hash("repo", "b" * 64, commit_sha="b" * 40)
    bc.new_block(proof=bc.proof_of_work())

    assert bc.verify_commit_ancestry() is True
    mock_run.assert_called_once()


@patch("scripts.blockchain.sbom.subprocess.run")
def test_verify_ancestry_detects_rewrite(mock_run):
    """verify_commit_ancestry fails when git reports no ancestry."""
    mock_run.return_value = MagicMock(returncode=1)

    bc = Blockchain()
    bc.add_sbom_hash("repo", "a" * 64, commit_sha="a" * 40)
    bc.new_block(proof=bc.proof_of_work())
    bc.add_sbom_hash("repo", "b" * 64, commit_sha="b" * 40)
    bc.new_block(proof=bc.proof_of_work())

    assert bc.verify_commit_ancestry() is False


def test_verify_ancestry_skips_legacy_blocks():
    """verify_commit_ancestry passes when no blocks carry commit_sha."""
    bc = Blockchain()
    bc.add_sbom_hash("repo", "a" * 64)
    bc.new_block(proof=bc.proof_of_work())
    bc.add_sbom_hash("repo", "b" * 64)
    bc.new_block(proof=bc.proof_of_work())

    assert bc.verify_commit_ancestry() is True


@patch("scripts.blockchain.sbom.subprocess.run")
def test_verify_ancestry_same_commit(mock_run):
    """verify_commit_ancestry skips check when consecutive commits are identical."""
    bc = Blockchain()
    sha = "f" * 40
    bc.add_sbom_hash("repo", "a" * 64, commit_sha=sha)
    bc.new_block(proof=bc.proof_of_work())
    bc.add_sbom_hash("repo", "b" * 64, commit_sha=sha)
    bc.new_block(proof=bc.proof_of_work())

    assert bc.verify_commit_ancestry() is True
    mock_run.assert_not_called()


# ---------------------------------------------------------------------------
# verify_index_worktree
# ---------------------------------------------------------------------------


@patch("scripts.blockchain.generate_sbom.subprocess.run")
def test_verify_index_worktree_clean(mock_run):
    """verify_index_worktree returns no errors when index matches working tree."""
    from scripts.blockchain.generate_sbom import verify_index_worktree

    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    errors = verify_index_worktree()
    assert errors == []


@patch("scripts.blockchain.generate_sbom.subprocess.run")
def test_verify_index_worktree_dirty(mock_run):
    """verify_index_worktree reports files with unstaged changes."""
    from scripts.blockchain.generate_sbom import verify_index_worktree

    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="src/main.js\nREADME.md\n",
        stderr="",
    )
    errors = verify_index_worktree()
    assert len(errors) == 1
    assert "2 file(s)" in errors[0]
    assert "src/main.js" in errors[0]


@patch("scripts.blockchain.generate_sbom.subprocess.run")
def test_verify_index_worktree_ignores_excluded(mock_run):
    """verify_index_worktree ignores sbom.json and chain.json changes."""
    from scripts.blockchain.generate_sbom import verify_index_worktree

    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="scripts/blockchain/sbom.json\nscripts/blockchain/chain.json\n",
        stderr="",
    )
    errors = verify_index_worktree()
    assert errors == []


@patch("scripts.blockchain.generate_sbom.subprocess.run")
def test_verify_index_worktree_git_failure(mock_run):
    """verify_index_worktree returns error when git diff fails."""
    from scripts.blockchain.generate_sbom import verify_index_worktree

    mock_run.return_value = MagicMock(
        returncode=128,
        stdout="",
        stderr="fatal: not a git repository",
    )
    errors = verify_index_worktree()
    assert len(errors) == 1
    assert "git diff failed" in errors[0]


# ---------------------------------------------------------------------------
# verify_chain_db_consistency
# ---------------------------------------------------------------------------


@patch("scripts.blockchain.db.connect")
@patch("scripts.blockchain.db.CHAIN_PATH")
def test_chain_db_consistency_matching(mock_chain_path, mock_connect):
    """verify_chain_db_consistency passes when chain SHAs are all in the DB."""
    from scripts.blockchain.db import verify_chain_db_consistency

    sha_a = "a" * 40
    sha_b = "b" * 40
    chain_data = [
        {"index": 1, "sbom_hashes": []},
        {"index": 2, "sbom_hashes": [{"repo": "r", "bom_hash": "x", "commit_sha": sha_a}]},
        {"index": 3, "sbom_hashes": [{"repo": "r", "bom_hash": "y", "commit_sha": sha_b}]},
    ]

    mock_chain_path.exists.return_value = True
    mock_chain_path.read_text.return_value = json.dumps(chain_data)

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [(sha_a,), (sha_b,)]
    mock_conn.cursor.return_value.__enter__ = lambda _: mock_cursor
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_connect.return_value = mock_conn

    errors = verify_chain_db_consistency()
    assert errors == []


@patch("scripts.blockchain.db.connect")
@patch("scripts.blockchain.db.CHAIN_PATH")
def test_chain_db_consistency_orphaned_commit(mock_chain_path, mock_connect):
    """verify_chain_db_consistency detects chain SHAs missing from DB."""
    from scripts.blockchain.db import verify_chain_db_consistency

    sha_known = "a" * 40
    sha_orphan = "b" * 40
    chain_data = [
        {"index": 1, "sbom_hashes": []},
        {"index": 2, "sbom_hashes": [{"repo": "r", "bom_hash": "x", "commit_sha": sha_known}]},
        {"index": 3, "sbom_hashes": [{"repo": "r", "bom_hash": "y", "commit_sha": sha_orphan}]},
    ]

    mock_chain_path.exists.return_value = True
    mock_chain_path.read_text.return_value = json.dumps(chain_data)

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [(sha_known,)]
    mock_conn.cursor.return_value.__enter__ = lambda _: mock_cursor
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_connect.return_value = mock_conn

    errors = verify_chain_db_consistency()
    assert len(errors) == 1
    assert "possible git history rewrite" in errors[0]
    assert sha_orphan in errors[0]


# ---------------------------------------------------------------------------
# SQL export escaping for non-JSON fields
# ---------------------------------------------------------------------------


@patch("scripts.blockchain.db.connect")
def test_export_sql_escapes_branch_and_commit(mock_connect, tmp_path):
    """SQL export escapes single quotes in commit_sha and branch fields."""
    from datetime import datetime, timezone

    from scripts.blockchain.db import export_sbom_version_sql

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        (
            1,
            "abc'def" + "0" * 33,  # commit_sha with quote
            "feature/it's-a-branch",  # branch with quote
            "c" * 64,
            1,
            {"ok": True},
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
    # Single quotes must be doubled in SQL
    assert "abc''def" in content
    assert "it''s-a-branch" in content
