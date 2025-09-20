-- Create the missing validation tables

-- Table to store individual song validation results
CREATE TABLE song_validations (
    id SERIAL PRIMARY KEY,
    canonical_mele_id INTEGER REFERENCES canonical_mele(canonical_mele_id) ON DELETE CASCADE,
    validation_session_id INTEGER REFERENCES validation_sessions(id) ON DELETE CASCADE,
    
    -- Quality metrics
    data_quality_score DECIMAL(5,2) NOT NULL,
    manual_review_required BOOLEAN DEFAULT FALSE,
    processing_status VARCHAR(20) DEFAULT 'processed', -- processed, flagged, failed
    
    -- Content analysis
    total_hawaiian_lines INTEGER DEFAULT 0,
    total_english_lines INTEGER DEFAULT 0,
    has_verse_structure BOOLEAN DEFAULT FALSE,
    has_english_translation BOOLEAN DEFAULT FALSE,
    
    -- Parsing metadata
    parser_version VARCHAR(50),
    parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_file_path TEXT,
    
    -- Notes and stray content
    processing_notes TEXT,
    stray_text JSONB, -- Array of unidentifiable text segments
    
    UNIQUE(canonical_mele_id, validation_session_id)
);

-- Table to store individual validation issues
CREATE TABLE validation_issues (
    id SERIAL PRIMARY KEY,
    song_validation_id INTEGER REFERENCES song_validations(id) ON DELETE CASCADE,
    
    -- Issue details
    issue_type VARCHAR(50) NOT NULL, -- maps to IssueType enum
    severity VARCHAR(20) NOT NULL,   -- low, medium, high, critical
    description TEXT NOT NULL,
    location VARCHAR(100),           -- where in the file the issue occurs
    
    -- Additional context
    raw_content TEXT,               -- problematic content sample
    suggested_action TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_song_validations_mele_id ON song_validations(canonical_mele_id);
CREATE INDEX idx_song_validations_session ON song_validations(validation_session_id);
CREATE INDEX idx_song_validations_quality ON song_validations(data_quality_score);
CREATE INDEX idx_song_validations_review ON song_validations(manual_review_required);
CREATE INDEX idx_validation_issues_song ON validation_issues(song_validation_id);
CREATE INDEX idx_validation_issues_type ON validation_issues(issue_type);
CREATE INDEX idx_validation_issues_severity ON validation_issues(severity);

-- Useful views for reporting
CREATE VIEW validation_summary AS
SELECT 
    vs.id as session_id,
    vs.session_name,
    vs.started_at,
    vs.completed_at,
    vs.total_songs,
    vs.songs_processed,
    vs.songs_flagged,
    vs.average_quality_score,
    COUNT(sv.id) as validated_songs,
    COUNT(CASE WHEN sv.manual_review_required THEN 1 END) as songs_needing_review,
    ROUND(AVG(sv.data_quality_score), 2) as calculated_avg_quality
FROM validation_sessions vs
LEFT JOIN song_validations sv ON vs.id = sv.validation_session_id
GROUP BY vs.id, vs.session_name, vs.started_at, vs.completed_at, 
         vs.total_songs, vs.songs_processed, vs.songs_flagged, vs.average_quality_score;

CREATE VIEW songs_needing_review AS
SELECT 
    cm.canonical_mele_id as id,
    cm.canonical_title_hawaiian,
    cm.primary_composer,
    sv.data_quality_score,
    sv.processing_status,
    sv.parsed_at,
    COUNT(vi.id) as issue_count,
    STRING_AGG(DISTINCT vi.issue_type, ', ') as issue_types
FROM canonical_mele cm
JOIN song_validations sv ON cm.canonical_mele_id = sv.canonical_mele_id
LEFT JOIN validation_issues vi ON sv.id = vi.song_validation_id
WHERE sv.manual_review_required = TRUE
GROUP BY cm.canonical_mele_id, cm.canonical_title_hawaiian, cm.primary_composer, 
         sv.data_quality_score, sv.processing_status, sv.parsed_at
ORDER BY sv.data_quality_score ASC, sv.parsed_at DESC;

-- Function to get validation details for a song
CREATE OR REPLACE FUNCTION get_song_validation_details(song_id INTEGER)
RETURNS TABLE (
    song_title TEXT,
    composer TEXT,
    quality_score DECIMAL,
    review_required BOOLEAN,
    issue_count BIGINT,
    issues JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cm.canonical_title_hawaiian::TEXT,
        cm.primary_composer::TEXT,
        sv.data_quality_score,
        sv.manual_review_required,
        COUNT(vi.id),
        COALESCE(
            jsonb_agg(
                jsonb_build_object(
                    'type', vi.issue_type,
                    'severity', vi.severity,
                    'description', vi.description,
                    'location', vi.location
                )
            ) FILTER (WHERE vi.id IS NOT NULL),
            '[]'::jsonb
        )
    FROM canonical_mele cm
    LEFT JOIN song_validations sv ON cm.canonical_mele_id = sv.canonical_mele_id
    LEFT JOIN validation_issues vi ON sv.id = vi.song_validation_id
    WHERE cm.canonical_mele_id = song_id
    GROUP BY cm.canonical_title_hawaiian, cm.primary_composer, 
             sv.data_quality_score, sv.manual_review_required;
END;
$$ LANGUAGE plpgsql;