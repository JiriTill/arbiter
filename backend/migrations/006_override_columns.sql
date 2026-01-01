-- Migration: 006_override_columns.sql
-- Add override tracking columns to rule_chunks

-- ============================================================================
-- Add override columns to rule_chunks
-- ============================================================================

-- Add overrides_chunk_id column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'rule_chunks' AND column_name = 'overrides_chunk_id'
    ) THEN
        ALTER TABLE rule_chunks 
        ADD COLUMN overrides_chunk_id BIGINT REFERENCES rule_chunks(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Add override_confidence column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'rule_chunks' AND column_name = 'override_confidence'
    ) THEN
        ALTER TABLE rule_chunks 
        ADD COLUMN override_confidence SMALLINT CHECK (override_confidence >= 0 AND override_confidence <= 100);
    END IF;
END $$;

-- Add override_evidence column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'rule_chunks' AND column_name = 'override_evidence'
    ) THEN
        ALTER TABLE rule_chunks 
        ADD COLUMN override_evidence TEXT;
    END IF;
END $$;

-- ============================================================================
-- Indexes
-- ============================================================================

-- Index for finding chunks that override a specific chunk
CREATE INDEX IF NOT EXISTS rule_chunks_overrides_idx 
ON rule_chunks(overrides_chunk_id) 
WHERE overrides_chunk_id IS NOT NULL;

-- Index for finding overriding chunks by confidence
CREATE INDEX IF NOT EXISTS rule_chunks_override_conf_idx 
ON rule_chunks(override_confidence DESC) 
WHERE overrides_chunk_id IS NOT NULL;

-- ============================================================================
-- Helper View: Override relationships
-- ============================================================================

CREATE OR REPLACE VIEW rule_chunk_overrides AS
SELECT 
    rc.id as expansion_chunk_id,
    rc.chunk_text as expansion_text,
    rc.page_number as expansion_page,
    rc.source_id as expansion_source_id,
    rc.overrides_chunk_id as base_chunk_id,
    bc.chunk_text as base_text,
    bc.page_number as base_page,
    bc.source_id as base_source_id,
    rc.override_confidence,
    rc.override_evidence,
    e.name as expansion_name
FROM rule_chunks rc
JOIN rule_chunks bc ON rc.overrides_chunk_id = bc.id
LEFT JOIN expansions e ON rc.expansion_id = e.id
WHERE rc.overrides_chunk_id IS NOT NULL;

-- ============================================================================
-- Function: Get all overrides for a base chunk
-- ============================================================================

CREATE OR REPLACE FUNCTION get_overrides_for_chunk(base_id BIGINT)
RETURNS TABLE (
    expansion_chunk_id BIGINT,
    override_confidence SMALLINT,
    override_evidence TEXT,
    expansion_name TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        rc.id,
        rc.override_confidence,
        rc.override_evidence,
        e.name
    FROM rule_chunks rc
    LEFT JOIN expansions e ON rc.expansion_id = e.id
    WHERE rc.overrides_chunk_id = base_id
    ORDER BY rc.override_confidence DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON COLUMN rule_chunks.overrides_chunk_id IS 'ID of base chunk that this expansion chunk overrides';
COMMENT ON COLUMN rule_chunks.override_confidence IS 'Confidence score 0-100 that this overrides the base chunk';
COMMENT ON COLUMN rule_chunks.override_evidence IS 'Quote showing override language from the expansion text';
