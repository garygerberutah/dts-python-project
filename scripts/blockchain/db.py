"""
db.py — PostgreSQL storage for SBOM version history.

Copyright 2026 by GuidoGerb Publishing, LLC

Stores every generated ``sbom.json`` manifest in the ``sbom_version`` table
so every commit's bill-of-materials is permanently auditable.
"""

import json
import platform
import subprocess
import sys
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parent.parent.parent


def _pg_host() -> str:
    """Return the PostgreSQL host — Windows gateway IP when running inside WSL2."""
    if platform.system() == "Linux" and Path("/proc/sys/fs/binfmt_misc/WSLInterop").exists():
        result = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True,
            text=True,
        )
        for token in result.stdout.split():
            if token.count(".") == 3:
                return token
    return "localhost"


def _dsn() -> str:
    host = _pg_host()
    return f"postgresql://assman:1324QEWRFD7sdf!1!@{host}:5432/asset_catalog"


CREATE_TABLE_SQL = """\
CREATE TABLE IF NOT EXISTS public.sbom_version (
    id              SERIAL          PRIMARY KEY,
    commit_sha      VARCHAR(40)     NOT NULL,
    branch          VARCHAR(256)    NOT NULL DEFAULT '',
    composite_sha256 VARCHAR(64)    NOT NULL,
    file_count      INTEGER         NOT NULL,
    sbom_content    JSONB           NOT NULL,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sbom_version_commit
    ON public.sbom_version (commit_sha);
"""

INSERT_SQL = """\
INSERT INTO public.sbom_version
    (commit_sha, branch, composite_sha256, file_count, sbom_content)
VALUES
    (%s, %s, %s, %s, %s)
RETURNING id;
"""


def _git_head_sha() -> str:
    """Return the current HEAD commit SHA (short 40-char)."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return "0" * 40
    return result.stdout.strip()


def _git_branch() -> str:
    """Return the current branch name."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip()


def ensure_table() -> None:
    """Create the ``sbom_version`` table if it does not already exist."""
    conn = psycopg2.connect(_dsn())
    try:
        with conn, conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
    finally:
        conn.close()
    print("[sbom-db] Table public.sbom_version ready.")


def store_sbom(manifest: dict, composite_sha256: str) -> int:
    """Insert an SBOM snapshot and return the row ``id``."""
    commit_sha = _git_head_sha()
    branch = _git_branch()
    file_count = manifest.get("file_count", len(manifest.get("files", [])))

    conn = psycopg2.connect(_dsn())
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                INSERT_SQL,
                (
                    commit_sha,
                    branch,
                    composite_sha256,
                    file_count,
                    json.dumps(manifest, sort_keys=True),
                ),
            )
            row_id = cur.fetchone()[0]
    finally:
        conn.close()

    print(f"[sbom-db] Stored SBOM version id={row_id} for commit {commit_sha[:8]}.")
    return row_id


def main() -> int:
    """CLI entry-point: create the table (idempotent)."""
    try:
        ensure_table()
    except psycopg2.OperationalError as exc:
        print(f"[sbom-db] Cannot connect to PostgreSQL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
