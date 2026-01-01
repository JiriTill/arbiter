-- ============================================================================
-- The Arbiter - Seed Data
-- Run this in Supabase SQL Editor AFTER the migration
-- ============================================================================

-- Insert sample games
INSERT INTO games (name, slug, bgg_id, cover_image_url) VALUES
  ('Root', 'root', 237182, 'https://cf.geekdo-images.com/JUAUWaVUzeBgzirhZNmHHw__imagepage/img/ZF-dta5ffawuKAkAt2LB-QTIv5M=/fit-in/900x600/filters:no_upscale():strip_icc()/pic4254509.jpg'),
  ('Wingspan', 'wingspan', 266192, 'https://cf.geekdo-images.com/yLZJCVLlIx4c7eJEWUNJ7w__imagepage/img/uIjeoKgHMcRtzRSR4MoUYl3nXxs=/fit-in/900x600/filters:no_upscale():strip_icc()/pic4458123.jpg'),
  ('Catan', 'catan', 13, 'https://cf.geekdo-images.com/W3Bsga_uLP9kO91gZ7H8yw__imagepage/img/M_3Vg1j2HlNgkv7PL2xl2BJE2bw=/fit-in/900x600/filters:no_upscale():strip_icc()/pic2419375.jpg'),
  ('Terraforming Mars', 'terraforming-mars', 167791, 'https://cf.geekdo-images.com/wg9oOLcsKvDesSUdZQ4rxw__imagepage/img/FS1RE8Ue6nk1pNbPI3l-OSapQGc=/fit-in/900x600/filters:no_upscale():strip_icc()/pic3536616.jpg'),
  ('Splendor', 'splendor', 148228, 'https://cf.geekdo-images.com/rwOMxx4q5yuElIvo-1-OFw__imagepage/img/qXpYXfJzT21tELMbG3V8WQio8z8=/fit-in/900x600/filters:no_upscale():strip_icc()/pic1904079.jpg')
ON CONFLICT (slug) DO NOTHING;

-- Insert sample sources (rulebook PDFs)
INSERT INTO game_sources (game_id, edition, source_type, source_url, is_official, needs_ocr) 
SELECT 
  g.id,
  '2nd Edition',
  'rulebook',
  'https://drive.google.com/uc?export=download&id=1iFVcWXdDfnlQrJo0HRET-TD1zr2oYIxq',
  true,
  false
FROM games g WHERE g.slug = 'root'
ON CONFLICT DO NOTHING;

INSERT INTO game_sources (game_id, edition, source_type, source_url, is_official, needs_ocr) 
SELECT 
  g.id,
  '1st Edition',
  'rulebook',
  'https://stonemaiergames.com/games/wingspan/rules/',
  true,
  false
FROM games g WHERE g.slug = 'wingspan'
ON CONFLICT DO NOTHING;

INSERT INTO game_sources (game_id, edition, source_type, source_url, is_official, needs_ocr) 
SELECT 
  g.id,
  '5th Edition',
  'rulebook',
  'https://www.catan.com/sites/default/files/2021-06/catan_base_rules_2020_200707.pdf',
  true,
  false
FROM games g WHERE g.slug = 'catan'
ON CONFLICT DO NOTHING;

INSERT INTO game_sources (game_id, edition, source_type, source_url, is_official, needs_ocr) 
SELECT 
  g.id,
  '1st Edition',
  'rulebook',
  'https://www.fryxgames.se/TersijMars/TMRULESFINAL.pdf',
  true,
  false
FROM games g WHERE g.slug = 'terraforming-mars'
ON CONFLICT DO NOTHING;

INSERT INTO game_sources (game_id, edition, source_type, source_url, is_official, needs_ocr) 
SELECT 
  g.id,
  '1st Edition',
  'rulebook',
  'https://cdn.1702.site/splendor/Splendor-Rules-EN.pdf',
  true,
  false
FROM games g WHERE g.slug = 'splendor'
ON CONFLICT DO NOTHING;

-- Verify
SELECT g.name, gs.edition, gs.source_type 
FROM games g 
LEFT JOIN game_sources gs ON g.id = gs.game_id
ORDER BY g.name;
