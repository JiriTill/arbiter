-- Migration: 008_feedback.sql
-- Create answer_feedback table for user feedback

CREATE TABLE IF NOT EXISTS answer_feedback (
    id BIGSERIAL PRIMARY KEY,
    ask_history_id BIGINT REFERENCES ask_history(id) ON DELETE CASCADE,
    feedback_type TEXT NOT NULL,
    -- Types: 'helpful' | 'wrong_quote' | 'wrong_interpretation' | 'missing_context' | 'wrong_source'
    selected_chunk_id BIGINT REFERENCES rule_chunks(id) ON DELETE SET NULL,
    user_note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS answer_feedback_ask_history_idx ON answer_feedback(ask_history_id);
CREATE INDEX IF NOT EXISTS answer_feedback_type_idx ON answer_feedback(feedback_type);
CREATE INDEX IF NOT EXISTS answer_feedback_created_idx ON answer_feedback(created_at);
