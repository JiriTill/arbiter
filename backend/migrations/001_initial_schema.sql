-- ============================================================================
-- The Arbiter - Phase 1 Database Schema
-- Migration: 001_initial_schema.sql
-- Created: 2025-12-31
-- Description: Initial schema with pgvector for board game rules RAG system
-- ============================================================================

-- ============================================================================
-- EXTENSIONS
-- ============================================================================

-- Enable pgvector for embedding storage and similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- GAMES CATALOG
-- ============================================================================

-- Core games table - represents base games
CREATE TABLE IF NOT EXISTS games (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,              -- URL-friendly identifier (e.g., "catan", "ticket-to-ride")
  bgg_id BIGINT,                          -- BoardGameGeek ID for cross-reference
  cover_image_url TEXT,                   -- Optional cover image
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Expansions for games
CREATE TABLE IF NOT EXISTS expansions (
  id BIGSERIAL PRIMARY KEY,
  game_id BIGINT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  code TEXT,                              -- Short code (e.g., "SEAFARERS", "CITIES_KNIGHTS")
  bgg_id BIGINT,                          -- BoardGameGeek ID for expansion
  release_date DATE,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- ============================================================================
-- SOURCE DOCUMENTS
-- ============================================================================

-- Source documents (rulebooks, FAQs, errata) for games
CREATE TABLE IF NOT EXISTS game_sources (
  id BIGSERIAL PRIMARY KEY,
  game_id BIGINT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
  expansion_id BIGINT REFERENCES expansions(id) ON DELETE SET NULL,
  
  -- Source identification
  edition TEXT NOT NULL,                  -- e.g., "5th Edition (2015)", "Revised 2023"
  source_type TEXT NOT NULL CHECK (source_type IN ('rulebook', 'faq', 'errata', 'reference_card')),
  source_url TEXT,                        -- Original download URL
  is_official BOOLEAN DEFAULT TRUE,       -- Official vs community-created
  
  -- Processing metadata
  file_hash TEXT,                         -- SHA-256 of source file for change detection
  needs_ocr BOOLEAN DEFAULT FALSE,        -- True if PDF needs OCR processing
  needs_reingest BOOLEAN DEFAULT FALSE,   -- Flag for re-processing queue
  verified_by TEXT,                       -- Optional: who verified this source
  
  -- Timestamps
  last_ingested_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  
  -- Ensure unique source per game/edition/type combo
  UNIQUE(game_id, expansion_id, edition, source_type)
);

-- ============================================================================
-- RULE CHUNKS (Core RAG Data)
-- ============================================================================

-- Chunked rule text with embeddings for similarity search
CREATE TABLE IF NOT EXISTS rule_chunks (
  id BIGSERIAL PRIMARY KEY,
  source_id BIGINT NOT NULL REFERENCES game_sources(id) ON DELETE CASCADE,
  
  -- Chunk location
  page_number INTEGER NOT NULL,
  chunk_index INTEGER NOT NULL,           -- Order within page
  section_title TEXT,                     -- Detected section heading
  
  -- Chunk content
  chunk_text TEXT NOT NULL,
  embedding vector(1536),                 -- OpenAI ada-002 embedding dimension
  
  -- Precedence system for rule overrides
  precedence_level INTEGER DEFAULT 1 NOT NULL,  -- 1=base, 2=expansion, 3=errata/faq
  overrides_chunk_id BIGINT REFERENCES rule_chunks(id) ON DELETE SET NULL,
  override_confidence REAL,               -- 0.0-1.0 confidence this overrides the target
  
  -- Game phase tagging (optional)
  phase_tags TEXT[],                      -- e.g., ['setup', 'combat', 'endgame']
  
  -- TTL for temporary rules (e.g., promotional content)
  expires_at TIMESTAMPTZ,
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  
  -- Ensure unique chunk per source/page/index
  UNIQUE(source_id, page_number, chunk_index)
);

-- ============================================================================
-- ASK HISTORY (Q&A Cache)
-- ============================================================================

-- History of questions and answers for caching and analytics
CREATE TABLE IF NOT EXISTS ask_history (
  id BIGSERIAL PRIMARY KEY,
  
  -- Question context
  game_id BIGINT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
  edition TEXT,                           -- Edition queried against
  expansions_used JSONB DEFAULT '[]',     -- List of expansion IDs included in query
  
  -- Question
  question TEXT NOT NULL,
  normalized_question TEXT,               -- Lowercased, trimmed for cache matching
  question_embedding vector(1536),        -- For semantic cache matching
  
  -- Answer
  verdict TEXT NOT NULL,
  confidence TEXT NOT NULL CHECK (confidence IN ('high', 'medium', 'low')),
  citations JSONB NOT NULL DEFAULT '[]',  -- Array of {chunk_id, quote, page, verified}
  
  -- Metadata
  response_time_ms INTEGER,               -- How long the query took
  model_used TEXT,                        -- e.g., "gpt-4-turbo"
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- ============================================================================
-- USER FEEDBACK
-- ============================================================================

-- Feedback on answer quality for improving the system
CREATE TABLE IF NOT EXISTS answer_feedback (
  id BIGSERIAL PRIMARY KEY,
  ask_history_id BIGINT NOT NULL REFERENCES ask_history(id) ON DELETE CASCADE,
  
  -- Feedback type
  feedback_type TEXT NOT NULL CHECK (feedback_type IN (
    'correct',           -- Answer was correct
    'incorrect',         -- Answer was wrong
    'incomplete',        -- Missing information
    'wrong_citation',    -- Citation was wrong/misquoted
    'better_source',     -- User found better source
    'other'
  )),
  
  -- Optional details
  selected_chunk_id BIGINT REFERENCES rule_chunks(id) ON DELETE SET NULL,  -- If user suggests better chunk
  user_note TEXT,                         -- Free-text feedback
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- ============================================================================
-- SOURCE HEALTH MONITORING
-- ============================================================================

-- Track health of source URLs for broken link detection
CREATE TABLE IF NOT EXISTS source_health (
  id BIGSERIAL PRIMARY KEY,
  source_id BIGINT NOT NULL REFERENCES game_sources(id) ON DELETE CASCADE,
  
  -- Check results
  last_checked_at TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('ok', 'changed', 'error', 'not_found')),
  http_code INTEGER,
  file_hash TEXT,                         -- New hash if changed
  content_length BIGINT,
  error TEXT,                             -- Error message if failed
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Games
CREATE INDEX IF NOT EXISTS games_slug_idx ON games(slug);
CREATE INDEX IF NOT EXISTS games_bgg_id_idx ON games(bgg_id) WHERE bgg_id IS NOT NULL;

-- Expansions
CREATE INDEX IF NOT EXISTS expansions_game_id_idx ON expansions(game_id);

-- Game Sources
CREATE INDEX IF NOT EXISTS game_sources_game_id_idx ON game_sources(game_id);
CREATE INDEX IF NOT EXISTS game_sources_needs_reingest_idx ON game_sources(needs_reingest) WHERE needs_reingest = TRUE;

-- Rule Chunks - Core indexes
CREATE INDEX IF NOT EXISTS rule_chunks_source_id_idx ON rule_chunks(source_id);
CREATE INDEX IF NOT EXISTS rule_chunks_expires_at_idx ON rule_chunks(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS rule_chunks_precedence_idx ON rule_chunks(source_id, precedence_level);

-- Rule Chunks - Vector similarity search using IVFFlat
-- Note: IVFFlat requires data to be present before index creation for optimal performance
-- For empty tables, this creates the index structure; rebuild after initial data load
CREATE INDEX IF NOT EXISTS rule_chunks_embedding_idx ON rule_chunks 
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Ask History
CREATE INDEX IF NOT EXISTS ask_history_game_id_created_idx ON ask_history(game_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ask_history_normalized_question_idx ON ask_history(normalized_question);
CREATE INDEX IF NOT EXISTS ask_history_created_at_idx ON ask_history(created_at DESC);

-- Ask History - Semantic cache using IVFFlat
CREATE INDEX IF NOT EXISTS ask_history_question_embedding_idx ON ask_history 
  USING ivfflat (question_embedding vector_cosine_ops) WITH (lists = 50);

-- Answer Feedback
CREATE INDEX IF NOT EXISTS answer_feedback_ask_history_id_idx ON answer_feedback(ask_history_id);

-- Source Health
CREATE INDEX IF NOT EXISTS source_health_source_id_idx ON source_health(source_id);
CREATE INDEX IF NOT EXISTS source_health_last_checked_idx ON source_health(last_checked_at DESC);

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

-- Games
COMMENT ON TABLE games IS 'Base games catalog with BGG cross-reference';
COMMENT ON COLUMN games.slug IS 'URL-friendly unique identifier for the game';
COMMENT ON COLUMN games.bgg_id IS 'BoardGameGeek game ID for external reference';

-- Expansions
COMMENT ON TABLE expansions IS 'Game expansions that may have their own rules';
COMMENT ON COLUMN expansions.code IS 'Short code for expansion identification in queries';

-- Game Sources
COMMENT ON TABLE game_sources IS 'Source documents (rulebooks, FAQs, errata) for rule extraction';
COMMENT ON COLUMN game_sources.source_type IS 'Document type: rulebook, faq, errata, or reference_card';
COMMENT ON COLUMN game_sources.file_hash IS 'SHA-256 hash for detecting source document changes';
COMMENT ON COLUMN game_sources.needs_ocr IS 'True if PDF is image-based and needs OCR processing';
COMMENT ON COLUMN game_sources.needs_reingest IS 'Flag for background job to re-process this source';

-- Rule Chunks
COMMENT ON TABLE rule_chunks IS 'Chunked rule text with embeddings for RAG similarity search';
COMMENT ON COLUMN rule_chunks.embedding IS 'OpenAI text-embedding-ada-002 vector (1536 dimensions)';
COMMENT ON COLUMN rule_chunks.precedence_level IS 'Rule priority: 1=base rulebook, 2=expansion, 3=errata/faq (higher wins)';
COMMENT ON COLUMN rule_chunks.overrides_chunk_id IS 'References the chunk this rule supersedes';
COMMENT ON COLUMN rule_chunks.override_confidence IS 'Confidence score (0-1) that this overrides the target chunk';
COMMENT ON COLUMN rule_chunks.phase_tags IS 'Game phases where this rule applies (setup, combat, etc.)';
COMMENT ON COLUMN rule_chunks.expires_at IS 'Optional TTL for temporary rules (e.g., promo content)';

-- Ask History
COMMENT ON TABLE ask_history IS 'History of Q&A for caching, analytics, and user history';
COMMENT ON COLUMN ask_history.normalized_question IS 'Lowercased, trimmed question for exact cache matching';
COMMENT ON COLUMN ask_history.question_embedding IS 'Vector for semantic similarity cache lookups';
COMMENT ON COLUMN ask_history.citations IS 'JSON array: [{chunk_id, quote, page, verified}]';
COMMENT ON COLUMN ask_history.confidence IS 'Answer confidence: high, medium, or low';

-- Answer Feedback
COMMENT ON TABLE answer_feedback IS 'User feedback for answer quality improvement';
COMMENT ON COLUMN answer_feedback.feedback_type IS 'Type of feedback: correct, incorrect, incomplete, wrong_citation, better_source, other';
COMMENT ON COLUMN answer_feedback.selected_chunk_id IS 'If user suggests a better source chunk';

-- Source Health
COMMENT ON TABLE source_health IS 'Monitoring table for source URL health checks';
COMMENT ON COLUMN source_health.status IS 'Check result: ok, changed, error, or not_found';

-- ============================================================================
-- ROW LEVEL SECURITY (Optional - enable if using Supabase Auth)
-- ============================================================================

-- Uncomment these if you want to enable RLS later:
-- ALTER TABLE games ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE expansions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE game_sources ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE rule_chunks ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE ask_history ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE answer_feedback ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE source_health ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- FUNCTIONS (Utility)
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_games_updated_at
  BEFORE UPDATE ON games
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_game_sources_updated_at
  BEFORE UPDATE ON game_sources
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VERIFICATION QUERIES (Run after migration to verify)
-- ============================================================================
-- SELECT * FROM pg_extension WHERE extname = 'vector';
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
-- SELECT indexname FROM pg_indexes WHERE schemaname = 'public';
-- \d rule_chunks
-- ============================================================================
