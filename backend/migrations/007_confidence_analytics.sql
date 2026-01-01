-- Migration: 007_confidence_analytics.sql
-- Add confidence_reason column and create analytics indexes

-- Add confidence_reason to ask_history
ALTER TABLE ask_history 
ADD COLUMN IF NOT EXISTS confidence_reason TEXT;

-- Index for confidence analytics
CREATE INDEX IF NOT EXISTS idx_ask_history_confidence 
ON ask_history(confidence);

-- Index for temporal analytics
CREATE INDEX IF NOT EXISTS idx_ask_history_created_at 
ON ask_history(created_at DESC);
