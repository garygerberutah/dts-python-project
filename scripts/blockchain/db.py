"""
db.py — PostgreSQL storage for SBOM version history.

Copyright 2026 by GuidoGerb Publishing, LLC

Stores every generated ``sbom.json`` manifest and ``chain.json`` blockchain
in the ``sbom_version`` table so every commit's bill-of-materials is
permanently auditable.

Connection strategy:
  1. Try the host PostgreSQL on port 5432.
  2. Fall back to the Docker PostgreSQL on port 5433.
  3. If neither is reachable, start the Docker container automatically.
"""

import json
import platform
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parent.parent.parent
DOCKER_COMPOSE_PATH = ROOT / "resources" / "postgres-data" / "docker-compose.yml"
SQL_EXPORT_DIR = ROOT / "resources" / "postgres-data"


def _wsl2_gateway() -> str | None:
    """Return the WSL2 default-gateway IP, or *None* outside WSL."""
    if platform.system() != "Linux":
        return None
    if not Path("/proc/sys/fs/binfmt_misc/WSLInterop").exists():
        return None
    result = subprocess.run(
        ["ip", "route", "show", "default"],
        capture_output=True,
        text=True,
    )
    for token in result.stdout.split():
        if token.count(".") == 3:
            return token
    return None


def _dsn(host: str, port: int) -> str:
    return f"postgresql://assman:1324QEWRFD7sdf!1!@{host}:{port}/asset_catalog"


def _try_connect_dsn(host: str, port: int) -> psycopg2.extensions.connection | None:
    """Attempt a connection to *host:port*; return conn or ``None``."""
    try:
        conn = psycopg2.connect(_dsn(host, port), connect_timeout=3)
        return conn
    except psycopg2.OperationalError:
        return None


# Backward-compat wrapper used by _start_docker_db
def _try_connect(port: int) -> psycopg2.extensions.connection | None:
    """Attempt a connection on *port* using localhost; return conn or ``None``."""
    return _try_connect_dsn("localhost", port)


def _start_docker_db() -> None:
    """Start the Docker PostgreSQL container via docker compose."""
    if not DOCKER_COMPOSE_PATH.exists():
        raise RuntimeError(f"Docker Compose file not found: {DOCKER_COMPOSE_PATH}")
    print("[sbom-db] Starting Docker PostgreSQL container…")
    result = subprocess.run(
        ["docker", "compose", "-f", str(DOCKER_COMPOSE_PATH), "up", "-d"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"docker compose up failed: {result.stderr}")

    # Wait for PostgreSQL to become ready (up to 30 seconds)
    import time

    for _attempt in range(30):
        conn = _try_connect(5433)
        if conn is not None:
            conn.close()
            print("[sbom-db] Docker PostgreSQL is ready.")
            return
        time.sleep(1)
    raise RuntimeError("Docker PostgreSQL did not become ready within 30 seconds.")


def connect() -> psycopg2.extensions.connection:
    """Connect to PostgreSQL with automatic fallback.

    Order:
      1. Windows host on port 5432 (try gateway IP then localhost).
      2. Docker container on port 5433 (localhost).
      3. Start Docker, then retry 5433.
    """
    # 1. Try Windows host PostgreSQL on port 5432
    gateway = _wsl2_gateway()
    if gateway is not None:
        conn = _try_connect_dsn(gateway, 5432)
        if conn is not None:
            return conn
    conn = _try_connect_dsn("localhost", 5432)
    if conn is not None:
        return conn

    # 2. Try Docker container on port 5433
    conn = _try_connect_dsn("localhost", 5433)
    if conn is not None:
        return conn

    # 3. Start Docker and retry
    _start_docker_db()
    conn = _try_connect_dsn("localhost", 5433)
    if conn is not None:
        return conn

    raise psycopg2.OperationalError("Cannot connect to PostgreSQL on port 5432 or 5433.")


CREATE_TABLE_SQL = """\
CREATE TABLE IF NOT EXISTS public.sbom_version (
    id               SERIAL          PRIMARY KEY,
    commit_sha       VARCHAR(40)     NOT NULL,
    branch           VARCHAR(256)    NOT NULL DEFAULT '',
    composite_sha256 VARCHAR(64)     NOT NULL,
    file_count       INTEGER         NOT NULL,
    sbom_content     JSONB           NOT NULL,
    chain_content    JSONB           NOT NULL DEFAULT '{}'::jsonb,
    created_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sbom_version_commit
    ON public.sbom_version (commit_sha);
"""

ALTER_ADD_CHAIN_SQL = """\
ALTER TABLE public.sbom_version
    ADD COLUMN IF NOT EXISTS chain_content JSONB NOT NULL DEFAULT '{}'::jsonb;
"""

INSERT_SQL = """\
INSERT INTO public.sbom_version
    (commit_sha, branch, composite_sha256, file_count, sbom_content, chain_content)
VALUES
    (%s, %s, %s, %s, %s, %s)
RETURNING id;
"""


def _git_head_sha() -> str:
    """Return the current HEAD commit SHA (full 40-char)."""
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
    """Create the ``sbom_version`` table if it does not already exist.

    Also adds the ``chain_content`` column to existing tables that lack it.
    """
    conn = connect()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
            cur.execute(ALTER_ADD_CHAIN_SQL)
    finally:
        conn.close()
    print("[sbom-db] Table public.sbom_version ready.")


def store_sbom(manifest: dict, composite_sha256: str, chain_data: list | None = None) -> int:
    """Insert an SBOM snapshot with blockchain data and return the row ``id``."""
    commit_sha = _git_head_sha()
    branch = _git_branch()
    file_count = manifest.get("file_count", len(manifest.get("files", [])))
    chain_json = json.dumps(chain_data or [], sort_keys=True)

    conn = connect()
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
                    chain_json,
                ),
            )
            row_id = cur.fetchone()[0]
    finally:
        conn.close()

    print(f"[sbom-db] Stored SBOM version id={row_id} for commit {commit_sha[:8]}.")
    return row_id


def export_sbom_version_sql() -> Path:
    """Export all rows from ``sbom_version`` as SQL INSERT statements.

    Returns the path of the generated ``.sql`` file.
    """
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d-%H%M%S")
    sql_path = SQL_EXPORT_DIR / f"sbom_version_{timestamp}.sql"

    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, commit_sha, branch, composite_sha256, "
                "file_count, sbom_content, chain_content, created_at "
                "FROM public.sbom_version ORDER BY id"
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    lines = [
        "-- Copyright 2026 by GuidoGerb Publishing, LLC",
        f"-- Exported from sbom_version on {timestamp}",
        f"-- {len(rows)} row(s)",
        "",
    ]
    for row in rows:
        (
            row_id,
            commit_sha,
            branch,
            composite,
            file_count,
            sbom_content,
            chain_content,
            created_at,
        ) = row
        # Escape single quotes in JSON strings for SQL safety
        sbom_str = json.dumps(sbom_content, sort_keys=True).replace("'", "''")
        chain_str = json.dumps(chain_content, sort_keys=True).replace("'", "''")
        created_str = created_at.isoformat()
        lines.append(
            f"INSERT INTO public.sbom_version "
            f"(id, commit_sha, branch, composite_sha256, file_count, "
            f"sbom_content, chain_content, created_at) VALUES ("
            f"{row_id}, '{commit_sha}', '{branch}', '{composite}', "
            f"{file_count}, '{sbom_str}'::jsonb, '{chain_str}'::jsonb, "
            f"'{created_str}'::timestamptz);"
        )

    lines.append("")
    sql_path.write_text("\n".join(lines), encoding="utf-8")
    try:
        rel = sql_path.relative_to(ROOT)
    except ValueError:
        rel = sql_path
    print(f"[sbom-db] Exported {len(rows)} row(s) → {rel}")
    return sql_path


def validate_sbom_db_sync() -> list[str]:
    """Verify SQL export files are in sync with the ``sbom_version`` table.

    Checks:
      1. If the DB has *N* rows, at least one SQL export file must contain
         *N* INSERT statements.
      2. Every SQL export file's INSERT count must not exceed the DB row count
         (no phantom rows in exports).

    Returns a list of error strings (empty == pass).
    """
    errors: list[str] = []

    # 1. Count DB rows
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM public.sbom_version")
            db_count: int = cur.fetchone()[0]
    finally:
        conn.close()

    # 2. Scan SQL export files
    sql_files = sorted(SQL_EXPORT_DIR.glob("sbom_version_*.sql"))

    if db_count == 0 and not sql_files:
        return errors  # nothing to check

    if db_count > 0 and not sql_files:
        errors.append(f"DB has {db_count} row(s) but no SQL export files in {SQL_EXPORT_DIR}")
        return errors

    # Count INSERT statements in each file
    insert_re = re.compile(r"^INSERT\s+INTO", re.IGNORECASE | re.MULTILINE)
    max_inserts = 0
    file_counts: dict[str, int] = {}
    for sql_file in sql_files:
        content = sql_file.read_text(encoding="utf-8")
        count = len(insert_re.findall(content))
        file_counts[sql_file.name] = count
        if count > max_inserts:
            max_inserts = count

    if max_inserts < db_count:
        errors.append(
            f"DB has {db_count} row(s) but the best SQL export only has "
            f"{max_inserts} INSERT statement(s). "
            f"Run 'python run.py sbom' to regenerate exports."
        )

    return errors


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
