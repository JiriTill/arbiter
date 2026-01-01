-- ============================================================================
-- The Arbiter - Complete Database Schema (Fixed for Supabase)
-- Run this in Supabase SQL Editor
-- ============================================================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- CORE TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS games (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  bgg_id BIGINT,
  cover_image_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS expansions (
  id BIGSERIAL PRIMARY KEY,
  game_id BIGINT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  code TEXT,
  bgg_id BIGINT,
  release_date DATE,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS game_sources (
  id BIGSERIAL PRIMARY KEY,
  game_id BIGINT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
  expansion_id BIGINT REFERENCES expansions(id) ON DELETE SET NULL,
  edition TEXT NOT NULL,
  source_type TEXT NOT NULL CHECK (source_type IN ('rulebook', 'faq', 'errata', 'reference_card')),
  source_url TEXT,
  is_official BOOLEAN DEFAULT TRUE,
  file_hash TEXT,
  needs_ocr BOOLEAN DEFAULT FALSE,
  needs_reingest BOOLEAN DEFAULT FALSE,
  verified_by TEXT,
  last_ingested_at TIMESTAMPTZ,
  last_health_check TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  UNIQUE(game_id, expansion_id, edition, source_type)
);

CREATE TABLE IF NOT EXISTS rule_chunks (
  id BIGSERIAL PRIMARY KEY,
  source_id BIGINT NOT NULL REFERENCES game_sources(id) ON DELETE CASCADE,
  page_number INTEGER NOT NULL,
  chunk_index INTEGER NOT NULL,
  section_title TEXT,
  chunk_text TEXT NOT NULL,
  embedding vector(1536),
  precedence_level INTEGER DEFAULT 1 NOT NULL,
  overrides_chunk_id BIGINT REFERENCES rule_chunks(id) ON DELETE SET NULL,
  override_confidence REAL,
  phase_tags TEXT[],
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  UNIQUE(source_id, page_number, chunk_index)
);

CREATE TABLE IF NOT EXISTS ask_history (
  id BIGSERIAL PRIMARY KEY,
  game_id BIGINT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
  edition TEXT,
  expansions_used JSONB DEFAULT '[]',
  question TEXT NOT NULL,
  normalized_question TEXT,
  question_embedding vector(1536),
  verdict TEXT NOT NULL,
  confidence TEXT NOT NULL CHECK (confidence IN ('high', 'medium', 'low')),
  citations JSONB NOT NULL DEFAULT '[]',
  response_time_ms INTEGER,
  model_used TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS answer_feedback (
  id BIGSERIAL PRIMARY KEY,
  ask_history_id BIGINT NOT NULL REFERENCES ask_history(id) ON DELETE CASCADE,
  feedback_type TEXT NOT NULL CHECK (feedback_type IN (
    'helpful', 'wrong_quote', 'wrong_interpretation', 'missing_context', 'wrong_source', 'other'
  )),
  selected_chunk_id BIGINT REFERENCES rule_chunks(id) ON DELETE SET NULL,
  user_note TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS source_health (
  id BIGSERIAL PRIMARY KEY,
  source_id BIGINT NOT NULL REFERENCES game_sources(id) ON DELETE CASCADE,
  last_checked_at TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('ok', 'changed', 'error', 'not_found')),
  http_code INTEGER,
  file_hash TEXT,
  content_length BIGINT,
  error TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS rate_limit_violations (
  id SERIAL PRIMARY KEY,
  client_ip VARCHAR(45) NOT NULL,
  endpoint VARCHAR(100) NOT NULL,
  method VARCHAR(10) NOT NULL,
  limit_type VARCHAR(50) NOT NULL,
  limit_value INTEGER NOT NULL,
  window_seconds INTEGER,
  session_id VARCHAR(255),
  user_agent TEXT,
  request_path TEXT,
  violated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS api_costs (
  id BIGSERIAL PRIMARY KEY,
  request_id TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  model TEXT NOT NULL,
  input_tokens INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0,
  cost_usd NUMERIC(10, 6) DEFAULT 0,
  cache_hit BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS source_suggestions (
  id BIGSERIAL PRIMARY KEY,
  game_id BIGINT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
  suggested_url TEXT NOT NULL,
  user_note TEXT,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS games_slug_idx ON games(slug);
CREATE INDEX IF NOT EXISTS games_bgg_id_idx ON games(bgg_id) WHERE bgg_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS expansions_game_id_idx ON expansions(game_id);
CREATE INDEX IF NOT EXISTS game_sources_game_id_idx ON game_sources(game_id);
CREATE INDEX IF NOT EXISTS game_sources_needs_reingest_idx ON game_sources(needs_reingest) WHERE needs_reingest = TRUE;
CREATE INDEX IF NOT EXISTS rule_chunks_source_id_idx ON rule_chunks(source_id);
CREATE INDEX IF NOT EXISTS rule_chunks_expires_at_idx ON rule_chunks(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS rule_chunks_precedence_idx ON rule_chunks(source_id, precedence_level);
CREATE INDEX IF NOT EXISTS ask_history_game_id_created_idx ON ask_history(game_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ask_history_normalized_question_idx ON ask_history(normalized_question);
CREATE INDEX IF NOT EXISTS ask_history_created_at_idx ON ask_history(created_at DESC);
CREATE INDEX IF NOT EXISTS answer_feedback_ask_history_id_idx ON answer_feedback(ask_history_id);
CREATE INDEX IF NOT EXISTS source_health_source_id_idx ON source_health(source_id);
CREATE INDEX IF NOT EXISTS source_health_last_checked_idx ON source_health(last_checked_at DESC);
CREATE INDEX IF NOT EXISTS idx_rate_violations_ip ON rate_limit_violations(client_ip, violated_at DESC);
CREATE INDEX IF NOT EXISTS idx_rate_violations_endpoint ON rate_limit_violations(endpoint, violated_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_costs_created ON api_costs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_costs_endpoint ON api_costs(endpoint);

-- Vector indexes (IVFFlat)
CREATE INDEX IF NOT EXISTS rule_chunks_embedding_idx ON rule_chunks 
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS ask_history_question_embedding_idx ON ask_history 
  USING ivfflat (question_embedding vector_cosine_ops) WITH (lists = 50);

-- ============================================================================
-- FULL-TEXT SEARCH
-- ============================================================================

ALTER TABLE rule_chunks 
ADD COLUMN IF NOT EXISTS tsv tsvector 
GENERATED ALWAYS AS (to_tsvector('english', COALESCE(chunk_text, ''))) STORED;

CREATE INDEX IF NOT EXISTS rule_chunks_tsv_idx ON rule_chunks USING GIN (tsv);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_games_updated_at ON games;
CREATE TRIGGER update_games_updated_at
  BEFORE UPDATE ON games
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_game_sources_updated_at ON game_sources;
CREATE TRIGGER update_game_sources_updated_at
  BEFORE UPDATE ON game_sources
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

CREATE OR REPLACE FUNCTION parse_search_query(query_text TEXT)
RETURNS tsquery AS $$
DECLARE
    result tsquery;
BEGIN
    BEGIN
        result := websearch_to_tsquery('english', query_text);
        RETURN result;
    EXCEPTION WHEN OTHERS THEN
        RETURN plainto_tsquery('english', query_text);
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- DONE
-- ============================================================================

SELECT 'Migration completed successfully!' as status;
