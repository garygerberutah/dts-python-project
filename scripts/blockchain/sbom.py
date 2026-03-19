"""
sbom.py — Append-only blockchain ledger for SBOM audit trail.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from time import time

CHAIN_PATH = Path(__file__).resolve().parent / "chain.json"
ROOT = Path(__file__).resolve().parent.parent.parent

# Proof-of-work difficulty: number of leading hex zeros required.
POW_DIFFICULTY = 4


class Blockchain:
    def __init__(self):
        self.chain: list[dict] = []
        self.pending_sbom_hashes: list[dict] = []
        # Create the genesis block
        self.new_block(previous_hash="1", proof=100)

    def new_block(self, proof: int, previous_hash: str | None = None) -> dict:
        """Create a new block and append it to the chain."""
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time(),
            "sbom_hashes": self.pending_sbom_hashes,
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.chain[-1]),
        }
        self.pending_sbom_hashes = []
        self.chain.append(block)
        return block

    def add_sbom_hash(self, repo_name: str, sha256_hash: str, commit_sha: str = "") -> int:
        """Queue an SBOM composite hash for the next block.

        When *commit_sha* is provided the hash entry is anchored to a
        specific git commit, allowing later verification that git history
        has not been rewritten.
        """
        entry: dict[str, str] = {
            "repo": repo_name,
            "bom_hash": sha256_hash,
        }
        if commit_sha:
            entry["commit_sha"] = commit_sha
        self.pending_sbom_hashes.append(entry)
        return self.last_block["index"] + 1

    @property
    def last_block(self) -> dict:
        return self.chain[-1]

    @staticmethod
    def hash(block: dict) -> str:
        """SHA-256 hash of a block (deterministic via sorted keys)."""
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    # ------------------------------------------------------------------
    # Proof-of-work
    # ------------------------------------------------------------------
    def proof_of_work(self) -> int:
        """Find a proof such that hash(last_proof, proof) has leading zeros."""
        last_proof = self.last_block["proof"]
        proof = 0
        prefix = "0" * POW_DIFFICULTY
        while True:
            guess = f"{last_proof}{proof}".encode()
            if hashlib.sha256(guess).hexdigest().startswith(prefix):
                return proof
            proof += 1

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save(self, path: Path | None = None) -> None:
        """Serialize the chain to a JSON file."""
        target = path or CHAIN_PATH
        target.write_text(
            json.dumps(self.chain, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path | None = None) -> "Blockchain":
        """Deserialize a chain from a JSON file, or return a fresh chain."""
        target = path or CHAIN_PATH
        if not target.exists() or target.stat().st_size == 0:
            return cls()
        chain_data = json.loads(target.read_text(encoding="utf-8"))
        if not chain_data:
            return cls()
        bc = cls.__new__(cls)
        bc.chain = chain_data
        bc.pending_sbom_hashes = []
        return bc

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------
    def verify_chain(self) -> bool:
        """Walk the chain and verify every block's previous_hash link."""
        for i in range(1, len(self.chain)):
            block = self.chain[i]
            prev = self.chain[i - 1]
            if block["previous_hash"] != self.hash(prev):
                print(
                    f"[blockchain] Integrity failure at block {block['index']}: "
                    f"previous_hash mismatch.",
                    file=sys.stderr,
                )
                return False
        return True

    # ------------------------------------------------------------------
    # Git-history anchoring
    # ------------------------------------------------------------------
    def verify_commit_ancestry(self) -> bool:
        """Verify that chain commit SHAs exist in git and are in order.

        For every pair of consecutive blocks that both carry a
        ``commit_sha``, checks that the earlier commit is an ancestor of
        (or equal to) the later commit.  This detects git history rewrites
        (rebase, amend, force-push, filter-branch) that would orphan the
        commits recorded in the chain.

        Returns ``True`` when all checks pass or when the chain has no
        commit-anchored entries (legacy blocks are silently skipped).
        """
        anchored: list[tuple[int, str]] = []
        for block in self.chain:
            for entry in block.get("sbom_hashes", []):
                sha = entry.get("commit_sha", "")
                if sha:
                    anchored.append((block["index"], sha))

        if len(anchored) < 2:
            return True

        for i in range(1, len(anchored)):
            idx_a, sha_a = anchored[i - 1]
            idx_b, sha_b = anchored[i]
            if sha_a == sha_b:
                continue
            result = subprocess.run(
                ["git", "merge-base", "--is-ancestor", sha_a, sha_b],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(
                    f"[blockchain] Commit ancestry failure: "
                    f"block {idx_a} commit {sha_a[:8]} is not an ancestor "
                    f"of block {idx_b} commit {sha_b[:8]}. "
                    f"Git history may have been rewritten.",
                    file=sys.stderr,
                )
                return False
        return True
