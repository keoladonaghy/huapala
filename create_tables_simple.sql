-- Create the missing validation tables (simplified version)

-- Table to store individual song validation results
CREATE TABLE song_validations (
    id SERIAL PRIMARY KEY,
    canonical_mele_id CHARACTER VARYING REFERENCES canonical_mele(canonical_mele_id) ON DELETE CASCADE,
    validation_session_id INTEGER REFERENCES validation_sessions(id) ON DELETE CASCADE,
    
    -- Quality metrics
    data_quality_score DECIMAL(5,2) NOT NULL,
    manual_review_required BOOLEAN DEFAULT FALSE,
    processing_status VARCHAR(20) DEFAULT 'processed',
    
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
    stray_text JSONB,
    
    UNIQUE(canonical_mele_id, validation_session_id)
);

-- Table to store individual validation issues
CREATE TABLE validation_issues (
    id SERIAL PRIMARY KEY,
    song_validation_id INTEGER REFERENCES song_validations(id) ON DELETE CASCADE,
    
    -- Issue details
    issue_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    location VARCHAR(100),
    
    -- Additional context
    raw_content TEXT,
    suggested_action TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Basic indexes
CREATE INDEX idx_song_validations_mele_id ON song_validations(canonical_mele_id);
CREATE INDEX idx_song_validations_session ON song_validations(validation_session_id);
CREATE INDEX idx_validation_issues_song ON validation_issues(song_validation_id);