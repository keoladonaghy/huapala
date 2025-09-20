-- ============================================================================
-- SONGBOOK ENTRIES TABLE SCHEMA
-- Table to store Hawaiian songbook index entries (~2100 records)
-- ============================================================================

-- Drop table if exists (for clean recreation)
DROP TABLE IF EXISTS songbook_entries CASCADE;

-- Create the main songbook entries table
CREATE TABLE songbook_entries (
    -- Primary key
    id SERIAL PRIMARY KEY,
    
    -- Timestamps and metadata
    timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Song title variations (all indexed for search)
    printed_song_title TEXT,
    eng_title_transl TEXT,
    modern_song_title TEXT,
    scripped_song_title TEXT,
    song_title TEXT,
    
    -- Songbook information
    songbook_name TEXT NOT NULL,
    page INTEGER,
    pub_year INTEGER,
    
    -- Content attributes
    diacritics TEXT CHECK (diacritics IN ('Yes', 'No', 'Inconsistent', 'Unknown')),
    
    -- People and attribution
    composer TEXT,
    additional_information TEXT,
    email_address TEXT,
    
    -- Foreign key to link with main song database
    canonical_mele_id TEXT REFERENCES canonical_mele(canonical_mele_id)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Song title search indexes (all title columns)
CREATE INDEX idx_songbook_printed_title ON songbook_entries USING gin(to_tsvector('english', printed_song_title));
CREATE INDEX idx_songbook_eng_title ON songbook_entries USING gin(to_tsvector('english', eng_title_transl));
CREATE INDEX idx_songbook_modern_title ON songbook_entries USING gin(to_tsvector('english', modern_song_title));
CREATE INDEX idx_songbook_scripped_title ON songbook_entries USING gin(to_tsvector('english', scripped_song_title));
CREATE INDEX idx_songbook_song_title ON songbook_entries USING gin(to_tsvector('english', song_title));

-- Additional required indexes
CREATE INDEX idx_songbook_name ON songbook_entries USING gin(to_tsvector('english', songbook_name));
CREATE INDEX idx_songbook_composer ON songbook_entries USING gin(to_tsvector('english', composer));

-- Efficient lookup indexes
CREATE INDEX idx_songbook_canonical_mele_id ON songbook_entries(canonical_mele_id);
CREATE INDEX idx_songbook_pub_year ON songbook_entries(pub_year);
CREATE INDEX idx_songbook_page ON songbook_entries(page);
CREATE INDEX idx_songbook_diacritics ON songbook_entries(diacritics);

-- Composite indexes for common queries
CREATE INDEX idx_songbook_name_page ON songbook_entries(songbook_name, page);
CREATE INDEX idx_songbook_year_name ON songbook_entries(pub_year, songbook_name);

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMPS
-- ============================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_songbook_entries_updated_at
    BEFORE UPDATE ON songbook_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE songbook_entries IS 'Index entries from Hawaiian songbooks with publication details and song references';
COMMENT ON COLUMN songbook_entries.printed_song_title IS 'Song title as printed in the songbook';
COMMENT ON COLUMN songbook_entries.eng_title_transl IS 'English translation of the song title';
COMMENT ON COLUMN songbook_entries.modern_song_title IS 'Modern or standardized version of the title';
COMMENT ON COLUMN songbook_entries.scripped_song_title IS 'Alternative scripted version of title';
COMMENT ON COLUMN songbook_entries.song_title IS 'Additional song title field';
COMMENT ON COLUMN songbook_entries.songbook_name IS 'Name of the songbook containing this entry';
COMMENT ON COLUMN songbook_entries.page IS 'Page number where song appears in songbook';
COMMENT ON COLUMN songbook_entries.pub_year IS 'Publication year of the songbook';
COMMENT ON COLUMN songbook_entries.diacritics IS 'Whether songbook uses Hawaiian diacritical marks: Yes/No/Inconsistent/Unknown';
COMMENT ON COLUMN songbook_entries.composer IS 'Composer or author of the song';
COMMENT ON COLUMN songbook_entries.additional_information IS 'Additional notes about the song or publication';
COMMENT ON COLUMN songbook_entries.email_address IS 'Contact email of the person who contributed this entry';
COMMENT ON COLUMN songbook_entries.canonical_mele_id IS 'Foreign key reference to canonical_mele table';

-- ============================================================================
-- SAMPLE QUERIES FOR TESTING
-- ============================================================================

-- Example queries (commented out for production):
/*
-- Search for songs by title
SELECT * FROM songbook_entries 
WHERE to_tsvector('english', printed_song_title) @@ plainto_tsquery('english', 'Hawaii');

-- Find all entries from a specific songbook
SELECT * FROM songbook_entries 
WHERE songbook_name ILIKE '%King%' 
ORDER BY page;

-- Search by composer
SELECT printed_song_title, songbook_name, page, pub_year 
FROM songbook_entries 
WHERE to_tsvector('english', composer) @@ plainto_tsquery('english', 'Charles King')
ORDER BY pub_year, page;

-- Find entries with missing canonical references
SELECT COUNT(*) FROM songbook_entries WHERE canonical_mele_id IS NULL;
*/