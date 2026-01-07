-- Migration 009: Add local image support to games table

ALTER TABLE games
ADD COLUMN IF NOT EXISTS image_filename TEXT,
ADD COLUMN IF NOT EXISTS image_alt_text TEXT;

-- We don't drop cover_image_url yet to allow fallback/migration, 
-- but eventually we might standardize on image_filename.
