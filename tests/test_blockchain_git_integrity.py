"""Tests for progressive blockchain verification against git history.

Copyright 2026 by GuidoGerb Publishing, LLC

Walks every git revision of ``chain.json`` and ``sbom.json`` and verifies:
  1. Chain internal integrity — each block's ``previous_hash`` matches the
     SHA-256 of the preceding block.
  2. SBOM–chain agreement — the composite SHA-256 of ``sbom.json`` at each
     revision matches the latest ``bom_hash`` recorded in ``chain.json``.
  3. Append-only growth — earlier blocks are never mutated across revisions.
  4. Proof-of-work validity — every block's proof satisfies the PoW constraint.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CHAIN_REL = "scripts/blockchain/chain.json"
SBOM_REL = "scripts/blockchain/sbom.json"
POW_DIFFICULTY = 4


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _git_log_commits(path: str) -> list[str]:
    """Return commit SHAs (oldest-first) that touch *path* in git history."""
    result = subprocess.run(
        ["git", "log", "--format=%H", "--reverse", "--follow", "--", path],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"git log failed: {result.stderr.strip()}")
    shas = [s.strip() for s in result.stdout.strip().splitlines() if s.strip()]
    if not shas:
        pytest.skip(f"No git history found for {path}")
    return shas


def _git_show(commit: str, path: str) -> str | None:
    """Return the contents of *path* at *commit*, or None if missing."""
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def _block_hash(block: dict) -> str:
    """Compute the SHA-256 hash of a block (deterministic via sorted keys)."""
    return hashlib.sha256(
        json.dumps(block, sort_keys=True).encode()
    ).hexdigest()


def _sbom_composite(manifest: dict) -> str:
    """Compute the composite SHA-256 of an SBOM manifest."""
    return hashlib.sha256(
        json.dumps(manifest, sort_keys=True).encode()
    ).hexdigest()


def _verify_chain_links(chain: list[dict]) -> None:
    """Assert that every block's previous_hash matches hash(prior block)."""
    assert chain[0]["previous_hash"] == "1", "Genesis block must have previous_hash='1'"
    for i in range(1, len(chain)):
        expected = _block_hash(chain[i - 1])
        actual = chain[i]["previous_hash"]
        assert actual == expected, (
            f"Block {chain[i]['index']}: previous_hash mismatch — "
            f"expected {expected[:16]}…, got {actual[:16]}…"
        )


def _verify_proof_of_work(chain: list[dict]) -> None:
    """Assert every non-genesis block's proof satisfies the PoW constraint."""
    prefix = "0" * POW_DIFFICULTY
    for i in range(1, len(chain)):
        last_proof = chain[i - 1]["proof"]
        proof = chain[i]["proof"]
        guess = f"{last_proof}{proof}".encode()
        digest = hashlib.sha256(guess).hexdigest()
        assert digest.startswith(prefix), (
            f"Block {chain[i]['index']}: proof {proof} does not satisfy "
            f"difficulty={POW_DIFFICULTY} (hash={digest[:16]}…)"
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def chain_commits() -> list[str]:
    """Commit SHAs (oldest-first) that modified chain.json."""
    return _git_log_commits(CHAIN_REL)


@pytest.fixture(scope="module")
def revision_pairs(chain_commits: list[str]) -> list[dict]:
    """Load chain.json and sbom.json at each commit.

    Returns a list of dicts:
        {"commit": <sha>, "chain": <list>, "sbom": <dict|None>}
    """
    pairs = []
    for sha in chain_commits:
        chain_raw = _git_show(sha, CHAIN_REL)
        sbom_raw = _git_show(sha, SBOM_REL)
        if chain_raw is None:
            continue
        entry: dict = {
            "commit": sha,
            "chain": json.loads(chain_raw),
            "sbom": json.loads(sbom_raw) if sbom_raw else None,
        }
        pairs.append(entry)
    assert pairs, "No valid chain.json / sbom.json revision pairs found"
    return pairs


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestChainIntegrityAcrossRevisions:
    """Chain internal integrity at every git revision."""

    def test_every_revision_has_valid_chain_links(self, revision_pairs):
        """previous_hash links are correct at each commit."""
        for entry in revision_pairs:
            _verify_chain_links(entry["chain"])

    def test_every_revision_has_genesis_block(self, revision_pairs):
        """Every revision starts with the same genesis block."""
        genesis = revision_pairs[0]["chain"][0]
        for entry in revision_pairs:
            assert entry["chain"][0] == genesis, (
                f"Genesis block differs at {entry['commit'][:7]}"
            )

    def test_chain_grows_monotonically(self, revision_pairs):
        """Each revision has at least as many blocks as the previous one."""
        prev_len = 0
        for entry in revision_pairs:
            current_len = len(entry["chain"])
            assert current_len >= prev_len, (
                f"Chain shrank at {entry['commit'][:7]}: "
                f"{prev_len} → {current_len}"
            )
            prev_len = current_len

    def test_chain_strictly_grows(self, revision_pairs):
        """Each subsequent revision added at least one new block."""
        for i in range(1, len(revision_pairs)):
            prev_len = len(revision_pairs[i - 1]["chain"])
            curr_len = len(revision_pairs[i]["chain"])
            assert curr_len > prev_len, (
                f"Chain did not grow between "
                f"{revision_pairs[i-1]['commit'][:7]} ({prev_len}) and "
                f"{revision_pairs[i]['commit'][:7]} ({curr_len})"
            )


class TestAppendOnlyProperty:
    """Earlier blocks must never be mutated across revisions."""

    def test_blocks_are_immutable_across_revisions(self, revision_pairs):
        """Every block present in revision N is identical in revision N+1."""
        for i in range(1, len(revision_pairs)):
            prev_chain = revision_pairs[i - 1]["chain"]
            curr_chain = revision_pairs[i]["chain"]
            shared = min(len(prev_chain), len(curr_chain))
            for j in range(shared):
                assert prev_chain[j] == curr_chain[j], (
                    f"Block {j} mutated between "
                    f"{revision_pairs[i-1]['commit'][:7]} and "
                    f"{revision_pairs[i]['commit'][:7]}"
                )

    def test_block_hashes_are_stable_across_revisions(self, revision_pairs):
        """Hash of each block stays the same across revisions."""
        prev_hashes: list[str] = []
        for entry in revision_pairs:
            curr_hashes = [_block_hash(b) for b in entry["chain"]]
            for j, h in enumerate(prev_hashes):
                assert curr_hashes[j] == h, (
                    f"Block {j} hash changed at {entry['commit'][:7]}"
                )
            prev_hashes = curr_hashes


class TestSbomChainAgreement:
    """sbom.json composite hash must match the latest bom_hash in chain.json."""

    def test_sbom_composite_matches_latest_block(self, revision_pairs):
        """At each revision, SHA-256(sbom.json) == chain's latest bom_hash."""
        for entry in revision_pairs:
            if entry["sbom"] is None:
                continue
            composite = _sbom_composite(entry["sbom"])

            # Find the last block that contains SBOM hashes
            last_bom = None
            for block in reversed(entry["chain"]):
                if block.get("sbom_hashes"):
                    last_bom = block["sbom_hashes"][-1]["bom_hash"]
                    break

            assert last_bom is not None, (
                f"No bom_hash found in chain at {entry['commit'][:7]}"
            )
            assert composite == last_bom, (
                f"SBOM composite mismatch at {entry['commit'][:7]}: "
                f"computed={composite[:16]}…, chain={last_bom[:16]}…"
            )

    def test_each_revision_has_unique_composite(self, revision_pairs):
        """Each revision should produce a different SBOM composite hash
        (the codebase changes between commits)."""
        composites = []
        for entry in revision_pairs:
            if entry["sbom"] is None:
                continue
            composites.append(_sbom_composite(entry["sbom"]))
        assert len(composites) == len(set(composites)), (
            "Duplicate SBOM composites found — each revision should differ"
        )


class TestProofOfWork:
    """Proof-of-work validation across all revisions."""

    def test_pow_valid_at_every_revision(self, revision_pairs):
        """Every block's proof satisfies the PoW difficulty at each revision."""
        for entry in revision_pairs:
            _verify_proof_of_work(entry["chain"])

    def test_pow_difficulty_matches_constant(self):
        """The test uses the same difficulty as the production code."""
        from scripts.blockchain.sbom import POW_DIFFICULTY as PROD_DIFFICULTY
        assert POW_DIFFICULTY == PROD_DIFFICULTY


class TestProgressiveBlockIndex:
    """Block indices must be sequential and contiguous."""

    def test_block_indices_are_sequential(self, revision_pairs):
        """Block indices at every revision go 1, 2, 3, … with no gaps."""
        for entry in revision_pairs:
            chain = entry["chain"]
            for i, block in enumerate(chain):
                expected_index = i + 1
                assert block["index"] == expected_index, (
                    f"Block index gap at {entry['commit'][:7]}: "
                    f"position {i} has index {block['index']}, expected {expected_index}"
                )


class TestCurrentCommittedState:
    """Verify the most recently committed revision of sbom.json / chain.json."""

    def test_current_chain_is_valid(self):
        """chain.json on disk passes full integrity check."""
        chain_path = ROOT / CHAIN_REL
        if not chain_path.exists():
            pytest.skip("chain.json not found on disk")
        chain = json.loads(chain_path.read_text(encoding="utf-8"))
        _verify_chain_links(chain)
        _verify_proof_of_work(chain)

    def test_latest_committed_sbom_matches_chain(self):
        """At HEAD, sbom.json composite matches chain.json's latest bom_hash.

        During a pipeline run the working-tree files are stale until stage 11
        regenerates them, so this test reads the **last committed** versions
        (``git show HEAD:<path>``) which are guaranteed to be in sync.
        """
        chain_raw = _git_show("HEAD", CHAIN_REL)
        sbom_raw = _git_show("HEAD", SBOM_REL)
        if chain_raw is None or sbom_raw is None:
            pytest.skip("chain.json or sbom.json not committed yet")

        chain = json.loads(chain_raw)
        sbom = json.loads(sbom_raw)
        composite = _sbom_composite(sbom)

        last_bom = None
        for block in reversed(chain):
            if block.get("sbom_hashes"):
                last_bom = block["sbom_hashes"][-1]["bom_hash"]
                break

        assert last_bom is not None, "No bom_hash found in chain.json at HEAD"
        assert composite == last_bom, (
            f"HEAD SBOM composite mismatch: "
            f"computed={composite[:16]}…, chain={last_bom[:16]}…"
        )

    def test_committed_chain_is_superset_of_disk(self):
        """On-disk chain.json must have at least as many blocks as HEAD."""
        chain_path = ROOT / CHAIN_REL
        if not chain_path.exists():
            pytest.skip("chain.json not on disk")
        chain_raw = _git_show("HEAD", CHAIN_REL)
        if chain_raw is None:
            pytest.skip("chain.json not committed yet")

        disk_chain = json.loads(chain_path.read_text(encoding="utf-8"))
        head_chain = json.loads(chain_raw)
        assert len(disk_chain) >= len(head_chain)
