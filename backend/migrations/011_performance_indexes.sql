-- Migration: Add performance indexes
-- Description: Create indexes for frequently queried columns

-- ============================================================================
-- Index for hybrid search on rule_chunks
-- ============================================================================

-- Source ID lookup (very common in search)
CREATE INDEX IF NOT EXISTS idx_rule_chunks_source_id 
ON rule_chunks(source_id);

-- Page number for sorting/filtering
CREATE INDEX IF NOT EXISTS idx_rule_chunks_page_number 
ON rule_chunks(page_number);

-- Combined index for source + page (commonly queried together)
CREATE INDEX IF NOT EXISTS idx_rule_chunks_source_page 
ON rule_chunks(source_id, page_number);

-- Full-text search index (if not already created)
CREATE INDEX IF NOT EXISTS idx_rule_chunks_tsv 
ON rule_chunks USING GIN(chunk_tsv);

-- Embedding vector index for similarity search
-- Using IVFFlat for approximate nearest neighbor
CREATE INDEX IF NOT EXISTS idx_rule_chunks_embedding 
ON rule_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- ============================================================================
-- Index for game_sources
-- ============================================================================

-- Game ID lookup
CREATE INDEX IF NOT EXISTS idx_game_sources_game_id 
ON game_sources(game_id);

-- Expansion lookup
CREATE INDEX IF NOT EXISTS idx_game_sources_expansion_id 
ON game_sources(expansion_id);

-- Needs reingest flag for worker queries
CREATE INDEX IF NOT EXISTS idx_game_sources_needs_reingest 
ON game_sources(needs_reingest) 
WHERE needs_reingest = TRUE;

-- ============================================================================
-- Index for ask_history
-- ============================================================================

-- Game-based history lookup
CREATE INDEX IF NOT EXISTS idx_ask_history_game_id 
ON ask_history(game_id);

-- Time-based sorting (most common)
CREATE INDEX IF NOT EXISTS idx_ask_history_created_at 
ON ask_history(created_at DESC);

-- Combined for efficient history queries
CREATE INDEX IF NOT EXISTS idx_ask_history_game_time 
ON ask_history(game_id, created_at DESC);

-- ============================================================================
-- Index for answer_feedback
-- ============================================================================

-- History ID lookup
CREATE INDEX IF NOT EXISTS idx_answer_feedback_history_id 
ON answer_feedback(ask_history_id);

-- Feedback type for analytics
CREATE INDEX IF NOT EXISTS idx_answer_feedback_type 
ON answer_feedback(feedback_type);

-- ============================================================================
-- Index for api_costs
-- ============================================================================

-- Date-based cost queries
CREATE INDEX IF NOT EXISTS idx_api_costs_created_at 
ON api_costs(created_at DESC);

-- Endpoint-based cost breakdown
CREATE INDEX IF NOT EXISTS idx_api_costs_endpoint 
ON api_costs(endpoint, created_at DESC);

-- ============================================================================
-- Index for games
-- ============================================================================

-- Slug lookup (common in URLs)
CREATE INDEX IF NOT EXISTS idx_games_slug 
ON games(slug);

-- BGG ID lookup
CREATE INDEX IF NOT EXISTS idx_games_bgg_id 
ON games(bgg_id) 
WHERE bgg_id IS NOT NULL;

-- ============================================================================
-- Index for expansions
-- ============================================================================

-- Game-based expansion lookup
CREATE INDEX IF NOT EXISTS idx_expansions_game_id 
ON expansions(game_id);

-- ============================================================================
-- Analyze tables for query planner
-- ============================================================================

ANALYZE rule_chunks;
ANALYZE game_sources;
ANALYZE ask_history;
ANALYZE answer_feedback;
ANALYZE api_costs;
ANALYZE games;
ANALYZE expansions;

-- ============================================================================
-- Create partial indexes for common queries
-- ============================================================================

-- Only active embeddings (not expired)
CREATE INDEX IF NOT EXISTS idx_rule_chunks_active_embeddings 
ON rule_chunks(source_id, id) 
WHERE embedding IS NOT NULL AND (expires_at IS NULL OR expires_at > NOW());

-- Verified feedback only
CREATE INDEX IF NOT EXISTS idx_feedback_verified 
ON answer_feedback(ask_history_id) 
WHERE feedback_type = 'helpful';
