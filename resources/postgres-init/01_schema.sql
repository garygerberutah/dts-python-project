-- Copyright 2026 by GuidoGerb Publishing, LLC
--
-- Auto-run on first container start by postgres:16-alpine entrypoint.
-- Creates the sbom_version table and index.

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
