-- Copyright 2026 by GuidoGerb Publishing, LLC
--
-- Create a restricted role for SBOM pipeline operations.
-- This role can only SELECT and INSERT on public.sbom_version — no UPDATE,
-- DELETE, DROP, or DDL.
--
-- Run as the PostgreSQL superuser (or the POSTGRES_USER from docker-compose):
--   psql -U assman -d asset_catalog -f 002-create-sbom-role.sql
--
-- Then set env vars in the pipeline:
--   export SBOM_DB_USER=sbom_writer
--   export SBOM_DB_PASSWORD='<choose-a-strong-password>'

-- 1. Create the role (idempotent)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sbom_writer') THEN
        CREATE ROLE sbom_writer WITH LOGIN PASSWORD 'CHANGE_ME_BEFORE_USE';
    END IF;
END
$$;

-- 2. Grant connect to the database
GRANT CONNECT ON DATABASE asset_catalog TO sbom_writer;

-- 3. Grant usage on the public schema
GRANT USAGE ON SCHEMA public TO sbom_writer;

-- 4. Grant SELECT and INSERT only on sbom_version
GRANT SELECT, INSERT ON TABLE public.sbom_version TO sbom_writer;

-- 5. Grant USAGE on the id sequence (required for INSERT … RETURNING id)
GRANT USAGE ON SEQUENCE public.sbom_version_id_seq TO sbom_writer;

-- 6. Revoke everything else explicitly (defense-in-depth)
REVOKE UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLE public.sbom_version FROM sbom_writer;
REVOKE CREATE ON SCHEMA public FROM sbom_writer;
