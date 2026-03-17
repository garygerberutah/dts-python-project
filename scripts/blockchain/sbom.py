"""
sbom.py — Append-only blockchain ledger for SBOM audit trail.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

import hashlib
import json
import sys
from pathlib import Path
from time import time

CHAIN_PATH = Path(__file__).resolve().parent / "chain.json"

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

    def add_sbom_hash(self, repo_name: str, sha256_hash: str) -> int:
        """Queue an SBOM composite hash for the next block."""
        self.pending_sbom_hashes.append(
            {
                "repo": repo_name,
                "bom_hash": sha256_hash,
            }
        )
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
