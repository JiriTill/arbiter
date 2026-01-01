-- Migration: 003_add_tsvector.sql
-- Add full-text search capabilities to rule_chunks using tsvector

-- ============================================================================
-- Step 1: Add tsvector column (generated from chunk_text)
-- ============================================================================

-- Note: PostgreSQL 12+ supports GENERATED ALWAYS AS ... STORED
-- This automatically updates the tsvector when chunk_text changes

ALTER TABLE rule_chunks 
ADD COLUMN IF NOT EXISTS tsv tsvector 
GENERATED ALWAYS AS (to_tsvector('english', COALESCE(chunk_text, ''))) STORED;

-- ============================================================================
-- Step 2: Create GIN index for fast full-text search
-- ============================================================================

-- GIN (Generalized Inverted Index) is optimal for tsvector queries
CREATE INDEX IF NOT EXISTS rule_chunks_tsv_idx 
ON rule_chunks 
USING GIN (tsv);

-- ============================================================================
-- Step 3: Create composite index for filtered searches
-- ============================================================================

-- This helps when searching within specific sources
CREATE INDEX IF NOT EXISTS rule_chunks_source_tsv_idx 
ON rule_chunks (source_id, tsv);

-- ============================================================================
-- Step 4: Backfill existing data
-- ============================================================================

-- The generated column should auto-populate, but we touch each row to ensure
-- This is a no-op update that triggers the column generation
UPDATE rule_chunks 
SET chunk_text = chunk_text 
WHERE tsv IS NULL;

-- ============================================================================
-- Step 5: Add helper function for query parsing
-- ============================================================================

-- Function to parse natural language query into tsquery
-- Handles common patterns like quoted phrases
CREATE OR REPLACE FUNCTION parse_search_query(query_text TEXT)
RETURNS tsquery AS $$
DECLARE
    result tsquery;
BEGIN
    -- First try to parse as a web-style query
    BEGIN
        result := websearch_to_tsquery('english', query_text);
        RETURN result;
    EXCEPTION WHEN OTHERS THEN
        -- Fallback to plainto_tsquery for simpler parsing
        RETURN plainto_tsquery('english', query_text);
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- Step 6: Create a ranking function for search results
-- ============================================================================

-- Ranks chunks by relevance to query
CREATE OR REPLACE FUNCTION rank_chunks(
    chunk_tsv tsvector,
    query tsquery,
    page_number INTEGER DEFAULT 1
)
RETURNS REAL AS $$
BEGIN
    -- Combine text rank with position bonus (earlier pages ranked higher)
    RETURN ts_rank_cd(chunk_tsv, query) * (1.0 / (1.0 + page_number * 0.01));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- Verification queries
-- ============================================================================

-- Check if column was added
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'rule_chunks' AND column_name = 'tsv';

-- Check index exists
-- SELECT indexname, indexdef 
-- FROM pg_indexes 
-- WHERE tablename = 'rule_chunks' AND indexname LIKE '%tsv%';

-- Test a search
-- SELECT id, page_number, ts_rank(tsv, plainto_tsquery('english', 'draw cards')) as rank
-- FROM rule_chunks
-- WHERE tsv @@ plainto_tsquery('english', 'draw cards')
-- ORDER BY rank DESC
-- LIMIT 10;

COMMENT ON COLUMN rule_chunks.tsv IS 'Full-text search vector generated from chunk_text';
