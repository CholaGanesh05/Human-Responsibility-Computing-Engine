-- ─────────────────────────────────────────────────────────────
-- HRCE — PostgreSQL Initialization Script
-- Runs automatically on first container startup.
-- ─────────────────────────────────────────────────────────────

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Confirm extensions
SELECT extname, extversion FROM pg_extension
WHERE extname IN ('vector', 'uuid-ossp', 'pg_trgm');
