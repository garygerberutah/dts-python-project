<!-- Copyright 2026 by GuidoGerb Publishing, LLC -->

# SBOM Blockchain Auditing

Generates a Software Bill of Materials (`sbom.json`) from every git-tracked
file at each commit and records an immutable audit trail in a local blockchain
(`chain.json`) and a PostgreSQL database.

## Pipeline Integration

Stage 11 of the master pipeline (`scripts/build_all.py`) runs automatically:

1. `generate_sbom.py` — walks `git ls-files`, hashes every file (SHA-256),
   writes `scripts/blockchain/sbom.json`.
2. `sbom.py` — loads the append-only blockchain from `chain.json`, appends a
   new block with the composite hash, mines a proof-of-work, verifies the
   chain, and saves.
3. `db.py` — stores the full SBOM manifest in the `public.sbom_version` table
   on the local PostgreSQL server.

## Standalone Commands

```bash
python run.py sbom        # Generate SBOM manifest only
python run.py sbom-db     # Create/verify the PostgreSQL table
```

## Database

Connection: `postgresql://assman:…@localhost:5432/asset_catalog`

Table `public.sbom_version`:

| Column            | Type         | Description                       |
|-------------------|--------------|-----------------------------------|
| id                | SERIAL PK    | Auto-incrementing row ID          |
| commit_sha        | VARCHAR(40)  | Git HEAD at generation time       |
| branch            | VARCHAR(256) | Current branch name               |
| composite_sha256  | VARCHAR(64)  | Hash of the entire SBOM manifest  |
| file_count        | INTEGER      | Number of tracked files           |
| sbom_content      | JSONB        | Full SBOM manifest                |
| created_at        | TIMESTAMPTZ  | Insertion timestamp               |