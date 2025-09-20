-- Add JSONB column for structured lyrics
ALTER TABLE canonical_mele ADD COLUMN structured_lyrics JSONB;

-- Add index for fast JSONB queries
CREATE INDEX idx_structured_lyrics_gin ON canonical_mele USING GIN (structured_lyrics);

-- Add index for specific JSONB queries
CREATE INDEX idx_lyrics_song_type ON canonical_mele USING GIN ((structured_lyrics -> 'song_type'));
CREATE INDEX idx_lyrics_has_chorus ON canonical_mele USING GIN ((structured_lyrics -> 'metadata' -> 'has_chorus'));

-- Example queries:

-- 1. Get complete structured song data
SELECT id, canonical_title_hawaiian, structured_lyrics 
FROM canonical_mele 
WHERE id = 123;

-- 2. Find all songs with choruses
SELECT id, canonical_title_hawaiian 
FROM canonical_mele 
WHERE structured_lyrics -> 'metadata' ->> 'has_chorus' = 'true';

-- 3. Search for specific Hawaiian text in any line
SELECT id, canonical_title_hawaiian
FROM canonical_mele
WHERE structured_lyrics @> '{"sections": [{"lines": [{"hawaiian_text": "aloha"}]}]}';

-- 4. Find hapa haole songs (mostly English)
SELECT id, canonical_title_hawaiian
FROM canonical_mele 
WHERE structured_lyrics ->> 'song_type' = 'hapa_haole';

-- 5. Get all verses from a song (excluding chorus)
SELECT jsonb_path_query_array(
    structured_lyrics, 
    '$.sections[*] ? (@.type == "verse")'
) as verses
FROM canonical_mele 
WHERE id = 123;

-- 6. Count lines by section type
SELECT 
    jsonb_path_query(structured_lyrics, '$.sections[*].type') as section_type,
    jsonb_array_length(jsonb_path_query(structured_lyrics, '$.sections[*].lines')) as line_count
FROM canonical_mele 
WHERE id = 123;