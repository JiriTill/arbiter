-- Migration: Source suggestions queue
CREATE TABLE IF NOT EXISTS source_suggestions (
  id BIGSERIAL PRIMARY KEY,
  game_id INTEGER NOT NULL REFERENCES games(id),
  suggested_url TEXT NOT NULL,
  user_note TEXT,
  status TEXT DEFAULT 'pending', -- pending, approved, rejected
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX source_suggestions_game_id_idx ON source_suggestions(game_id);
CREATE INDEX source_suggestions_status_idx ON source_suggestions(status);
