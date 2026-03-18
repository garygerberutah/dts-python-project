"""
sync_db.py — Rebuild PostgreSQL sbom_version table from chain.json.

Copyright 2026 by GuidoGerb Publishing, LLC

The blockchain in ``chain.json`` is the authoritative source of truth.
This script reconstructs the PostgreSQL ``sbom_version`` table from it,
making the database fully portable across environments.

Usage:
    python -m scripts.blockchain.sync_db          # rebuild from chain.json
    python run.py sync-db                          # via run.py entry point
"""

import json
import sys
from pathlib import Path

import psycopg2

from scripts.blockchain.db import (
    ensure_table,
    get_connection,
)
from scripts.blockchain.sbom import CHAIN_PATH, Blockchain

ROOT = Path(__file__).resolve().parent.parent.parent

INSERT_SYNC_SQL = """\
INSERT INTO public.sbom_version
    (commit_sha, branch, composite_sha256, file_count, sbom_content)
VALUES
    (%s, %s, %s, %s, %s)
ON CONFLICT DO NOTHING;
"""


def sync(chain_path: Path = CHAIN_PATH) -> int:
    """Rebuild the sbom_version table from the blockchain.

    Returns the number of blocks synced (blocks with SBOM hashes).
    """
    bc = Blockchain.load(chain_path)
    if not bc.verify_chain():
        print("[sync-db] Blockchain integrity check FAILED.", file=sys.stderr)
        raise RuntimeError("Blockchain verification failed — refusing to sync.")

    ensure_table()
    conn = get_connection()
    synced = 0
    try:
        with conn, conn.cursor() as cur:
            # Iterate every block (skip genesis which has no SBOM data)
            for block in bc.chain:
                for entry in block.get("sbom_hashes", []):
                    bom_hash = entry.get("bom_hash", "")
                    if not bom_hash:
                        continue
                    # We don't have the original commit_sha/branch/manifest
                    # in chain.json — store what we have from the block.
                    cur.execute(
                        INSERT_SYNC_SQL,
                        (
                            "0" * 40,  # commit_sha unknown from chain
                            entry.get("repo", "unknown"),
                            bom_hash,
                            0,  # file_count unknown from chain
                            json.dumps(
                                {"synced_from": "chain.json", "block_index": block["index"]}
                            ),
                        ),
                    )
                    synced += 1
    finally:
        conn.close()

    print(f"[sync-db] Synced {synced} SBOM entries from chain.json to PostgreSQL.")
    return synced


def main() -> int:
    """CLI entry point."""
    try:
        sync()
    except psycopg2.OperationalError as exc:
        print(f"[sync-db] Cannot connect to PostgreSQL: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"[sync-db] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
