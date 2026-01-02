
-- Fix broken BGG Image URLs by removing the filter parameters
-- This regex replacer removes the "/fit-in/.../filters:.../" part, keeping the original image path.

UPDATE games
SET cover_image_url = regexp_replace(
    cover_image_url, 
    '/fit-in/[^/]+/filters:[^/]+/', 
    '/'
)
WHERE cover_image_url LIKE '%filters:%';

-- Verify fixes
SELECT name, cover_image_url FROM games;
