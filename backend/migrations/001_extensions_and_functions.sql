-- RECO Database Layer: Extensions and shared functions
-- Run first before any schema migrations.

BEGIN;

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Reusable trigger to maintain updated_at on mutable tables.
CREATE OR REPLACE FUNCTION reco_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION reco_set_updated_at() IS
    'Sets updated_at to current timestamp on row update.';

COMMIT;
