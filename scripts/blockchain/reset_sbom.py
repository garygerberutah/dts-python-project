"""
reset_sbom.py — Reset SBOM manifest, blockchain, and (optionally) the database.

Copyright 2026 by GuidoGerb Publishing, LLC

Deletes the local sbom.json and chain.json artifacts and optionally
truncates the sbom_version database table.  Run this script externally
(not via the pipeline) to perform a clean reset.

Usage:
    python scripts/blockchain/reset_sbom.py                # Local files only
    python scripts/blockchain/reset_sbom.py --include-db   # Files + DB table
    python scripts/blockchain/reset_sbom.py --include-db --include-exports  # + SQL exports
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SBOM_PATH = Path(__file__).resolve().parent / "sbom.json"
CHAIN_PATH = Path(__file__).resolve().parent / "chain.json"
SQL_EXPORT_DIR = ROOT / "resources" / "postgres-data"


def reset_local_files() -> None:
    """Remove sbom.json and chain.json if they exist."""
    for path in (SBOM_PATH, CHAIN_PATH):
        if path.exists():
            path.unlink()
            print(f"[reset] Deleted {path.relative_to(ROOT)}")
        else:
            print(f"[reset] Already absent: {path.relative_to(ROOT)}")


def reset_sql_exports() -> None:
    """Remove all sbom_version_*.sql export files."""
    sql_files = sorted(SQL_EXPORT_DIR.glob("sbom_version_*.sql"))
    if not sql_files:
        print("[reset] No SQL export files found.")
        return
    for sql_file in sql_files:
        sql_file.unlink()
    print(f"[reset] Deleted {len(sql_files)} SQL export file(s).")


def reset_database() -> None:
    """Truncate the sbom_version table in PostgreSQL."""
    # Ensure project root is on sys.path for imports
    import sys

    root = Path(__file__).resolve().parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    try:
        from scripts.blockchain.db import connect
    except ImportError:
        print(
            "[reset] Cannot import db.py — ensure psycopg2 is installed.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        conn = connect()
    except Exception as exc:
        print(f"[reset] Cannot connect to PostgreSQL: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        with conn, conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE public.sbom_version RESTART IDENTITY")
        print("[reset] Truncated public.sbom_version (all rows deleted, id reset).")
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reset SBOM manifest, blockchain, and optionally the database.",
    )
    parser.add_argument(
        "--include-db",
        action="store_true",
        help="Also truncate the sbom_version table in PostgreSQL.",
    )
    parser.add_argument(
        "--include-exports",
        action="store_true",
        help="Also delete sbom_version_*.sql export files.",
    )
    args = parser.parse_args()

    reset_local_files()

    if args.include_exports:
        reset_sql_exports()

    if args.include_db:
        reset_database()

    print("[reset] Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
