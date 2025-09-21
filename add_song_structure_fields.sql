-- Add song_type and structure_type columns to mele_sources table
-- Add the new classification fields to support Hawaiian song categorization

-- Add song_type column with allowed values
ALTER TABLE mele_sources ADD COLUMN IF NOT EXISTS song_type VARCHAR(20) DEFAULT 'mele' 
    CHECK (song_type IN ('mele', 'hapa-haole', 'local-song', 'other'));

-- Add structure_type column with allowed values  
ALTER TABLE mele_sources ADD COLUMN IF NOT EXISTS structure_type VARCHAR(30) DEFAULT 'unknown'
    CHECK (structure_type IN ('2-line-strophic', '4-line-strophic', 'verse-chorus', 'through-composed', 'other', 'unknown'));

-- Set all existing songs to 'mele' type (as specified by user)
UPDATE mele_sources SET song_type = 'mele' WHERE song_type IS NULL OR song_type = '';

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_mele_sources_song_type ON mele_sources(song_type);
CREATE INDEX IF NOT EXISTS idx_mele_sources_structure_type ON mele_sources(structure_type);

-- Example queries for the new fields:

-- 1. Find all mele songs
-- SELECT canonical_mele_id, source_specific_title FROM mele_sources WHERE song_type = 'mele';

-- 2. Find all four-line strophic songs
-- SELECT canonical_mele_id, source_specific_title FROM mele_sources WHERE structure_type = '4-line-strophic';

-- 3. Find all verse-chorus songs
-- SELECT canonical_mele_id, source_specific_title FROM mele_sources WHERE structure_type = 'verse-chorus';

-- 4. Count songs by structure type
-- SELECT structure_type, COUNT(*) FROM mele_sources GROUP BY structure_type;