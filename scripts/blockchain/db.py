"""
db.py — PostgreSQL storage for SBOM version history.

Copyright 2026 by GuidoGerb Publishing, LLC

Stores every generated ``sbom.json`` manifest in the ``sbom_version`` table
so every commit's bill-of-materials is permanently auditable.

Connection strategy (ordered):
  1. Localhost PostgreSQL (port 5432) — your development machine
  2. Docker container ``ggp3d-postgres`` (port 5433) — auto-started if needed
"""

import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parent.parent.parent

# --- Connection parameters ------------------------------------------------

_PG_USER = "assman"
_PG_PASSWORD = "1324QEWRFD7sdf!1!"
_PG_DB = "asset_catalog"
_LOCALHOST_PORT = 5432
_DOCKER_PORT = 5433
_DOCKER_CONTAINER = "ggp3d-postgres"


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


def _dsn(host: str = "localhost", port: int = _LOCALHOST_PORT) -> str:
    return f"postgresql://{_PG_USER}:{_PG_PASSWORD}@{host}:{port}/{_PG_DB}"


def _try_connect(host: str, port: int) -> psycopg2.extensions.connection | None:
    """Attempt a connection; return it on success or None on failure."""
    try:
        conn = psycopg2.connect(_dsn(host, port), connect_timeout=3)
        return conn
    except psycopg2.OperationalError:
        return None


def _ensure_docker_pg() -> bool:
    """Start the Docker Compose PostgreSQL service if not already running."""
    if not shutil.which("docker"):
        print("[sbom-db] Docker not found — cannot start fallback PostgreSQL.", file=sys.stderr)
        return False

    # Check if container is already running
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", _DOCKER_CONTAINER],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip() == "true":
        return True

    # Start via docker compose
    print("[sbom-db] Starting Docker PostgreSQL…")
    compose_file = ROOT / "docker-compose.yml"
    if not compose_file.exists():
        print("[sbom-db] docker-compose.yml not found.", file=sys.stderr)
        return False

    result = subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "up", "-d", "--wait"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[sbom-db] Docker Compose failed: {result.stderr}", file=sys.stderr)
        return False

    print("[sbom-db] Docker PostgreSQL started on port 5433.")
    return True


def get_connection() -> psycopg2.extensions.connection:
    """Connect to PostgreSQL: try localhost:5432 first, then Docker:5433.

    Raises ``psycopg2.OperationalError`` if neither is reachable.
    """
    host = _pg_host()

    # 1. Try localhost (or WSL2 gateway)
    conn = _try_connect(host, _LOCALHOST_PORT)
    if conn is not None:
        return conn

    # 2. Try existing Docker container on port 5433
    conn = _try_connect("localhost", _DOCKER_PORT)
    if conn is not None:
        return conn

    # 3. Start Docker and retry
    if _ensure_docker_pg():
        conn = _try_connect("localhost", _DOCKER_PORT)
        if conn is not None:
            return conn

    raise psycopg2.OperationalError(
        f"Cannot connect to PostgreSQL on {host}:{_LOCALHOST_PORT} "
        f"or localhost:{_DOCKER_PORT} (Docker)."
    )


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
    conn = get_connection()
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

    conn = get_connection()
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
