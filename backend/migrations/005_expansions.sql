-- Migration: 005_expansions.sql
-- Expansions support for games with expansion content

-- ============================================================================
-- Expansions Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS expansions (
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign key to games
    game_id BIGINT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    
    -- Expansion info
    name TEXT NOT NULL,
    code TEXT NOT NULL,  -- Short identifier: 'riverfolk', 'underworld', etc.
    description TEXT,
    release_date DATE,
    
    -- For display order
    display_order INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Ensure unique code per game
    UNIQUE(game_id, code)
);

-- Index for game lookups
CREATE INDEX IF NOT EXISTS expansions_game_id_idx ON expansions(game_id);

-- ============================================================================
-- Update game_sources to link to expansions
-- ============================================================================

-- Add expansion_id column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'game_sources' AND column_name = 'expansion_id'
    ) THEN
        ALTER TABLE game_sources 
        ADD COLUMN expansion_id BIGINT REFERENCES expansions(id) ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS game_sources_expansion_id_idx ON game_sources(expansion_id);

-- ============================================================================
-- Update rule_chunks for expansion tracking and precedence
-- ============================================================================

-- Add expansion_id column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'rule_chunks' AND column_name = 'expansion_id'
    ) THEN
        ALTER TABLE rule_chunks 
        ADD COLUMN expansion_id BIGINT REFERENCES expansions(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Add precedence_level column if it doesn't exist
-- 1 = base game rules
-- 2 = expansion rules  
-- 3 = errata/FAQ (highest precedence)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'rule_chunks' AND column_name = 'precedence_level'
    ) THEN
        ALTER TABLE rule_chunks 
        ADD COLUMN precedence_level INTEGER NOT NULL DEFAULT 1;
    END IF;
END $$;

-- Indexes for filtering
CREATE INDEX IF NOT EXISTS rule_chunks_expansion_id_idx ON rule_chunks(expansion_id);
CREATE INDEX IF NOT EXISTS rule_chunks_precedence_idx ON rule_chunks(precedence_level);

-- Composite index for searching within expansions
CREATE INDEX IF NOT EXISTS rule_chunks_source_expansion_idx 
ON rule_chunks(source_id, expansion_id);

-- ============================================================================
-- Helper View: Chunks with expansion info
-- ============================================================================

CREATE OR REPLACE VIEW rule_chunks_with_expansion AS
SELECT 
    rc.*,
    e.name as expansion_name,
    e.code as expansion_code,
    gs.source_type,
    g.name as game_name
FROM rule_chunks rc
LEFT JOIN expansions e ON rc.expansion_id = e.id
JOIN game_sources gs ON rc.source_id = gs.id
JOIN games g ON gs.game_id = g.id;

-- ============================================================================
-- Update function for timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION update_expansion_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS expansions_updated_at ON expansions;
CREATE TRIGGER expansions_updated_at
    BEFORE UPDATE ON expansions
    FOR EACH ROW
    EXECUTE FUNCTION update_expansion_timestamp();

COMMENT ON TABLE expansions IS 'Game expansions with their own rulesets';
COMMENT ON COLUMN rule_chunks.precedence_level IS '1=base, 2=expansion, 3=errata/faq';
