-- Migration: 004_source_health.sql
-- Source health monitoring for detecting URL changes

-- ============================================================================
-- Source Health Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS source_health (
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign key to game_sources
    source_id BIGINT NOT NULL REFERENCES game_sources(id) ON DELETE CASCADE,
    
    -- Check results
    last_checked_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ok', 'unreachable', 'changed', 'error')),
    http_code INTEGER,
    
    -- Content metadata
    file_hash TEXT,
    content_length BIGINT,
    etag TEXT,
    last_modified TEXT,
    
    -- Error details
    error TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- Indexes
-- ============================================================================

-- Index for finding latest check per source
CREATE INDEX IF NOT EXISTS source_health_source_id_idx 
ON source_health(source_id);

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS source_health_last_checked_idx 
ON source_health(last_checked_at DESC);

-- Composite index for finding problems
CREATE INDEX IF NOT EXISTS source_health_status_idx 
ON source_health(status, last_checked_at DESC);

-- Partial index for recent checks only
CREATE INDEX IF NOT EXISTS source_health_recent_idx 
ON source_health(source_id, last_checked_at DESC) 
WHERE last_checked_at > NOW() - INTERVAL '7 days';

-- ============================================================================
-- Helper Views
-- ============================================================================

-- Latest health status per source
CREATE OR REPLACE VIEW source_health_latest AS
SELECT DISTINCT ON (source_id)
    sh.id,
    sh.source_id,
    gs.source_url,
    g.name as game_name,
    gs.edition,
    sh.status,
    sh.http_code,
    sh.file_hash,
    sh.content_length,
    sh.etag,
    sh.last_modified,
    sh.error,
    sh.last_checked_at,
    gs.needs_reingest
FROM source_health sh
JOIN game_sources gs ON sh.source_id = gs.id
JOIN games g ON gs.game_id = g.id
ORDER BY source_id, last_checked_at DESC;

-- Sources with problems
CREATE OR REPLACE VIEW source_health_problems AS
SELECT * FROM source_health_latest
WHERE status IN ('unreachable', 'changed', 'error');

-- ============================================================================
-- Add columns to game_sources if needed
-- ============================================================================

-- Add last_health_check column to game_sources
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'game_sources' AND column_name = 'last_health_check'
    ) THEN
        ALTER TABLE game_sources ADD COLUMN last_health_check TIMESTAMPTZ;
    END IF;
END $$;

-- Add file_hash column if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'game_sources' AND column_name = 'file_hash'
    ) THEN
        ALTER TABLE game_sources ADD COLUMN file_hash TEXT;
    END IF;
END $$;

-- ============================================================================
-- Cleanup function
-- ============================================================================

-- Keep only last 30 days of health checks
CREATE OR REPLACE FUNCTION cleanup_old_health_checks()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM source_health 
    WHERE last_checked_at < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE source_health IS 'Historical health check results for game sources';
