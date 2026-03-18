"""Tests for scripts/blockchain/sbom.py — append-only blockchain ledger.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

import json

from scripts.blockchain.sbom import Blockchain, POW_DIFFICULTY


def test_genesis_block_created():
    """A new blockchain has exactly one genesis block."""
    bc = Blockchain()
    assert len(bc.chain) == 1
    assert bc.chain[0]["index"] == 1
    assert bc.chain[0]["previous_hash"] == "1"
    assert bc.chain[0]["proof"] == 100


def test_new_block_appends():
    """new_block creates a second block linked to genesis."""
    bc = Blockchain()
    bc.add_sbom_hash(repo_name="test-repo", sha256_hash="abc123")
    proof = bc.proof_of_work()
    block = bc.new_block(proof=proof)
    assert block["index"] == 2
    assert len(bc.chain) == 2
    assert block["sbom_hashes"][0]["repo"] == "test-repo"


def test_pending_cleared_after_new_block():
    """Pending SBOM hashes are cleared after mining a new block."""
    bc = Blockchain()
    bc.add_sbom_hash(repo_name="repo", sha256_hash="hash1")
    bc.new_block(proof=bc.proof_of_work())
    assert bc.pending_sbom_hashes == []


def test_add_sbom_hash_returns_next_index():
    """add_sbom_hash returns the index of the upcoming block."""
    bc = Blockchain()
    next_idx = bc.add_sbom_hash(repo_name="repo", sha256_hash="h")
    assert next_idx == 2


def test_last_block_property():
    """last_block returns the most recent block in the chain."""
    bc = Blockchain()
    assert bc.last_block["index"] == 1
    bc.add_sbom_hash(repo_name="r", sha256_hash="h")
    bc.new_block(proof=bc.proof_of_work())
    assert bc.last_block["index"] == 2


def test_hash_deterministic():
    """hash() produces the same digest for the same block dict."""
    bc = Blockchain()
    block = bc.chain[0]
    h1 = Blockchain.hash(block)
    h2 = Blockchain.hash(block)
    assert h1 == h2
    assert len(h1) == 64


def test_proof_of_work_valid():
    """proof_of_work returns a proof meeting the difficulty target."""
    bc = Blockchain()
    proof = bc.proof_of_work()
    last_proof = bc.last_block["proof"]
    guess = f"{last_proof}{proof}".encode()
    import hashlib

    digest = hashlib.sha256(guess).hexdigest()
    assert digest.startswith("0" * POW_DIFFICULTY)


def test_verify_chain_valid():
    """A properly built chain passes verification."""
    bc = Blockchain()
    bc.add_sbom_hash(repo_name="repo", sha256_hash="abc")
    bc.new_block(proof=bc.proof_of_work())
    bc.add_sbom_hash(repo_name="repo", sha256_hash="def")
    bc.new_block(proof=bc.proof_of_work())
    assert bc.verify_chain() is True


def test_verify_chain_tampered():
    """A chain with a tampered block fails verification."""
    bc = Blockchain()
    bc.add_sbom_hash(repo_name="repo", sha256_hash="abc")
    bc.new_block(proof=bc.proof_of_work())
    # Tamper with the genesis block timestamp
    bc.chain[0]["timestamp"] = 0
    assert bc.verify_chain() is False


def test_save_and_load(tmp_path):
    """save() and load() round-trip the chain correctly."""
    chain_file = tmp_path / "chain.json"
    bc = Blockchain()
    bc.add_sbom_hash(repo_name="repo", sha256_hash="abc")
    bc.new_block(proof=bc.proof_of_work())
    bc.save(path=chain_file)

    loaded = Blockchain.load(path=chain_file)
    assert len(loaded.chain) == 2
    assert loaded.chain[1]["sbom_hashes"][0]["bom_hash"] == "abc"
    assert loaded.verify_chain() is True


def test_load_empty_file(tmp_path):
    """load() returns a fresh chain when the file is empty."""
    chain_file = tmp_path / "chain.json"
    chain_file.write_text("", encoding="utf-8")
    bc = Blockchain.load(path=chain_file)
    assert len(bc.chain) == 1
    assert bc.chain[0]["index"] == 1


def test_load_nonexistent_file(tmp_path):
    """load() returns a fresh chain when the file doesn't exist."""
    chain_file = tmp_path / "nonexistent.json"
    bc = Blockchain.load(path=chain_file)
    assert len(bc.chain) == 1


def test_save_creates_valid_json(tmp_path):
    """save() writes valid JSON with sorted keys."""
    chain_file = tmp_path / "chain.json"
    bc = Blockchain()
    bc.save(path=chain_file)
    data = json.loads(chain_file.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 1
    assert "index" in data[0]


def test_multiple_sbom_hashes_in_one_block():
    """Multiple SBOM hashes can be queued before mining."""
    bc = Blockchain()
    bc.add_sbom_hash(repo_name="repo-a", sha256_hash="h1")
    bc.add_sbom_hash(repo_name="repo-b", sha256_hash="h2")
    bc.new_block(proof=bc.proof_of_work())
    block = bc.chain[1]
    assert len(block["sbom_hashes"]) == 2
    repos = {h["repo"] for h in block["sbom_hashes"]}
    assert repos == {"repo-a", "repo-b"}
