<!-- Copyright 2026 by GuidoGerb Publishing, LLC -->

# scripts/blockchain/ — SBOM Generation & Blockchain Auditing

Generates a Software Bill of Materials (`sbom.json`) from every git-tracked
file at each commit and records an immutable audit trail in a local blockchain
(`chain.json`) and a PostgreSQL database.

## Directory Layout

```
scripts/blockchain/
├── __init__.py          # Package marker
├── generate_sbom.py     # Build SBOM manifest from git-tracked files
├── sbom.py              # Append-only blockchain with proof-of-work
├── db.py                # PostgreSQL storage, export, and validation
├── sbom.json            # Current SBOM manifest (generated, excluded from SBOM)
├── chain.json           # Current blockchain state (generated, excluded from SBOM)
└── README.md
```

## Pipeline Integration

Stage 12 of the master pipeline (`scripts/build_all.py`) executes three
sub-stages in sequence. Stage 11 validates that SQL exports are in sync with
the database before the SBOM stage runs.

### Stage 12 — SBOM (blockchain)

1. **`generate_sbom.py`** — walks `git ls-files`, computes SHA-256 for every
   tracked file, writes `scripts/blockchain/sbom.json`. The `sbom.json` and
   `chain.json` files are excluded from the manifest to avoid circular
   dependency.
2. **`sbom.py`** — loads the append-only blockchain from `chain.json`, queues
   the composite SBOM hash, mines a proof-of-work block (4 leading hex zeros),
   verifies the full chain integrity, and saves.
3. **`db.py`** — stores the full SBOM manifest and blockchain state in the
   `public.sbom_version` table, then exports all rows as SQL INSERT statements.

### Stage 11 — Validate (SBOM-DB sync)

Runs `db.validate_sbom_db_sync()` to verify that at least one SQL export file
in `resources/postgres-data/` contains as many INSERT statements as the
database has rows.

## Standalone Commands

```bash
python run.py sbom        # Generate SBOM manifest + blockchain + DB store
python run.py sbom-db     # Create/verify the PostgreSQL table (idempotent)
```

## Modules

### generate_sbom.py

Builds the SBOM manifest by walking all files from `git ls-files`, computing a
SHA-256 hash for each, and writing the result to `sbom.json`.

| Function           | Description                                      |
|--------------------|--------------------------------------------------|
| `_git_ls_files()`  | Return sorted list of git-tracked paths          |
| `_sha256(path)`    | Compute SHA-256 hex digest of a file             |
| `generate()`       | Generate manifest, return `(dict, composite_hex)`|

**Manifest structure:**

```json
{
  "version": "1.0",
  "timestamp": "2026-03-18T23:46:51.152307+00:00",
  "file_count": 176,
  "files": [
    { "path": "scripts/ui/build.py", "sha256": "abc123…" }
  ]
}
```

The **composite hash** is the SHA-256 of the entire manifest JSON (sorted keys,
deterministic).

### sbom.py

Manages an append-only blockchain ledger for SBOM audit.

| Method / Property        | Description                                     |
|--------------------------|-------------------------------------------------|
| `Blockchain()`           | Create chain with genesis block                 |
| `add_sbom_hash(repo, h)` | Queue a composite hash for the next block      |
| `proof_of_work()`        | Find proof with 4 leading hex zeros             |
| `new_block(proof, prev)` | Create and append a new block                   |
| `verify_chain()`         | Walk chain, verify every `previous_hash` link   |
| `hash(block)`            | Deterministic SHA-256 of a block                |
| `save(path)`             | Serialize chain to JSON file                    |
| `Blockchain.load(path)`  | Deserialize chain from JSON (or return fresh)   |

**Block structure:**

```json
{
  "index": 2,
  "timestamp": 1710799611.123,
  "sbom_hashes": [{ "repo": "ggp-python-project", "bom_hash": "abc…" }],
  "proof": 71832,
  "previous_hash": "0000abcd…"
}
```

Proof-of-work difficulty: `POW_DIFFICULTY = 4` (4 leading hex zeros).

### db.py

PostgreSQL storage for SBOM version history with automatic connection fallback
and SQL export.

**Connection strategy:**

1. Try the host PostgreSQL on **port 5432** (WSL2 gateway IP first, then
   `localhost`).
2. Fall back to Docker PostgreSQL on **port 5433** (`localhost`).
3. If neither is reachable, start the Docker container via `docker compose up`
   and retry port 5433.

| Function                    | Description                                        |
|-----------------------------|----------------------------------------------------|
| `connect()`                 | Connect with automatic fallback                    |
| `ensure_table()`            | Create `sbom_version` table (idempotent)           |
| `store_sbom(manifest, …)`   | Insert SBOM + chain data, return row `id`          |
| `export_sbom_version_sql()` | Export all rows as SQL INSERT file                 |
| `validate_sbom_db_sync()`   | Verify SQL exports match DB row count              |

## Database Schema

Connection: `postgresql://assman:…@localhost:5432/asset_catalog`

Table `public.sbom_version`:

| Column            | Type         | Description                              |
|-------------------|--------------|------------------------------------------|
| id                | SERIAL PK    | Auto-incrementing row ID                 |
| commit_sha        | VARCHAR(40)  | Git HEAD at generation time              |
| branch            | VARCHAR(256) | Current branch name                      |
| composite_sha256  | VARCHAR(64)  | SHA-256 of the entire SBOM manifest      |
| file_count        | INTEGER      | Number of tracked files                  |
| sbom_content      | JSONB        | Full SBOM manifest JSON                  |
| chain_content     | JSONB        | Full blockchain state at insertion time  |
| created_at        | TIMESTAMPTZ  | Insertion timestamp                      |

**Indexes:** `idx_sbom_version_commit` on `commit_sha`.

## SQL Exports

Every pipeline run exports all database rows as SQL INSERT statements to
`resources/postgres-data/sbom_version_<timestamp>.sql`. These files serve as
portable backups and are validated by the SBOM-DB sync stage.

## Docker PostgreSQL

The Docker container is defined in `resources/postgres-data/docker-compose.yml`
and initialised by `resources/postgres-data/init/001-create-tables.sql`. It
runs on port **5433** to avoid conflicting with a host PostgreSQL on 5432.

```bash
docker compose -f resources/postgres-data/docker-compose.yml up -d
```