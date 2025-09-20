#!/usr/bin/env python3
"""
Database-integrated validation system for Huapala
Extends the existing validation system to work with Neon PostgreSQL
"""

import os
import sys
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path so we can import scripts modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.data_validation_system import HuapalaValidator, SongValidationResult, ValidationIssue

class DatabaseValidator(HuapalaValidator):
    """Validation system integrated with Neon PostgreSQL database"""
    
    def __init__(self, connection_string: str = None):
        super().__init__()
        
        # Use provided connection string or environment variable
        self.connection_string = connection_string or os.getenv('DATABASE_URL')
        if not self.connection_string:
            raise ValueError("Database connection string required. Set DATABASE_URL environment variable.")
        
        self.conn = None
        self.current_session_id = None
        
    def connect(self):
        """Connect to the database"""
        try:
            self.conn = psycopg2.connect(self.connection_string)
            self.conn.autocommit = False  # We'll manage transactions
            self.logger.info("Connected to Neon PostgreSQL database")
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.logger.info("Disconnected from database")
    
    def start_validation_session(self, session_name: str) -> int:
        """Start a new validation session and return session ID"""
        if not self.conn:
            self.connect()
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO validation_sessions (session_name, started_at, status)
                    VALUES (%s, %s, 'running')
                    RETURNING id
                """, (session_name, datetime.now()))
                
                session_id = cursor.fetchone()[0]
                self.current_session_id = session_id
                self.conn.commit()
                
                self.logger.info(f"Started validation session '{session_name}' with ID {session_id}")
                return session_id
                
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Failed to start validation session: {e}")
            raise
    
    def validate_and_store_song(self, song_data: Dict, canonical_mele_id: int) -> SongValidationResult:
        """Validate a song and store results in database"""
        
        # Run the standard validation
        validation_result = self.validate_song(song_data)
        
        # Store in database
        self.store_validation_result(validation_result, canonical_mele_id, song_data)
        
        return validation_result
    
    def store_validation_result(self, result: SongValidationResult, canonical_mele_id: int, song_data: Dict):
        """Store validation results in the database"""
        if not self.conn:
            self.connect()
        
        if not self.current_session_id:
            raise ValueError("No active validation session. Call start_validation_session() first.")
        
        try:
            with self.conn.cursor() as cursor:
                # Insert song validation record
                cursor.execute("""
                    INSERT INTO song_validations (
                        canonical_mele_id, validation_session_id, data_quality_score,
                        manual_review_required, processing_status, total_hawaiian_lines,
                        total_english_lines, has_verse_structure, has_english_translation,
                        parser_version, source_file_path, processing_notes, stray_text
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    canonical_mele_id,
                    self.current_session_id,
                    result.data_quality_score,
                    result.manual_review_required,
                    result.processing_status,
                    len(result.hawaiian_lines),
                    len(result.english_lines),
                    song_data.get('has_verse_structure', False),
                    song_data.get('has_english_translation', False),
                    "1.0",  # Parser version
                    song_data.get('source_file', ''),
                    result.processing_notes,
                    psycopg2.extras.Json(result.stray_text) if result.stray_text else None
                ))
                
                song_validation_id = cursor.fetchone()[0]
                
                # Insert validation issues
                for issue in result.validation_issues:
                    cursor.execute("""
                        INSERT INTO validation_issues (
                            song_validation_id, issue_type, severity, description,
                            location, raw_content, suggested_action
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        song_validation_id,
                        issue.issue_type.value,
                        issue.severity.value,
                        issue.description,
                        issue.location,
                        issue.raw_content,
                        issue.suggested_action
                    ))
                
                self.conn.commit()
                self.logger.info(f"Stored validation results for song {canonical_mele_id}")
                
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Failed to store validation results: {e}")
            raise
    
    def complete_validation_session(self):
        """Mark the current validation session as complete and update statistics"""
        if not self.conn or not self.current_session_id:
            return
        
        try:
            with self.conn.cursor() as cursor:
                # Calculate session statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_processed,
                        COUNT(CASE WHEN manual_review_required THEN 1 END) as flagged,
                        ROUND(AVG(data_quality_score), 2) as avg_quality
                    FROM song_validations 
                    WHERE validation_session_id = %s
                """, (self.current_session_id,))
                
                stats = cursor.fetchone()
                total_processed, flagged, avg_quality = stats
                
                # Update session record
                cursor.execute("""
                    UPDATE validation_sessions 
                    SET completed_at = %s, songs_processed = %s, songs_flagged = %s,
                        average_quality_score = %s, status = 'completed'
                    WHERE id = %s
                """, (
                    datetime.now(),
                    total_processed,
                    flagged,
                    avg_quality,
                    self.current_session_id
                ))
                
                self.conn.commit()
                self.logger.info(f"Completed validation session {self.current_session_id}: "
                               f"{total_processed} songs, {flagged} flagged, {avg_quality} avg quality")
                
                self.current_session_id = None
                
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Failed to complete validation session: {e}")
            raise
    
    def get_songs_needing_review(self) -> List[Dict]:
        """Get all songs that require manual review"""
        if not self.conn:
            self.connect()
        
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM songs_needing_review ORDER BY data_quality_score ASC")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_validation_summary(self, session_id: int = None) -> Dict:
        """Get validation summary for a session or all sessions"""
        if not self.conn:
            self.connect()
        
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            if session_id:
                cursor.execute("SELECT * FROM validation_summary WHERE session_id = %s", (session_id,))
                result = cursor.fetchone()
                return dict(result) if result else {}
            else:
                cursor.execute("SELECT * FROM validation_summary ORDER BY started_at DESC")
                return [dict(row) for row in cursor.fetchall()]
    
    def get_song_validation_details(self, canonical_mele_id: int) -> Dict:
        """Get detailed validation information for a specific song"""
        if not self.conn:
            self.connect()
        
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM get_song_validation_details(%s)", (canonical_mele_id,))
            result = cursor.fetchone()
            return dict(result) if result else {}

# Example usage functions
def batch_validate_songs(song_files: List[str], parser, db_validator: DatabaseValidator):
    """Validate multiple songs and store results"""
    
    session_name = f"batch_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_id = db_validator.start_validation_session(session_name)
    
    try:
        for song_file in song_files:
            try:
                # Parse the song
                parsed_song, validation_result = parser.parse_file(song_file)
                
                # Find or create canonical_mele record (you'd implement this)
                canonical_mele_id = find_or_create_canonical_mele(parsed_song)
                
                # Validate and store
                db_validator.validate_and_store_song(
                    parser._prepare_validation_data(parsed_song),
                    canonical_mele_id
                )
                
                print(f"Processed: {song_file}")
                
            except Exception as e:
                print(f"Failed to process {song_file}: {e}")
                continue
        
        db_validator.complete_validation_session()
        
    except Exception as e:
        print(f"Batch validation failed: {e}")
        raise
    finally:
        db_validator.disconnect()

def find_or_create_canonical_mele(parsed_song) -> int:
    """Find existing or create new canonical_mele record"""
    # This would implement logic to match songs or create new records
    # For now, return a placeholder
    return 1

if __name__ == "__main__":
    # Test the database validator
    db_validator = DatabaseValidator()
    
    try:
        # Test connection
        db_validator.connect()
        
        # Test session management
        session_id = db_validator.start_validation_session("test_session")
        print(f"Started session: {session_id}")
        
        # Get validation summary
        summary = db_validator.get_validation_summary()
        print(f"Validation summary: {summary}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db_validator.disconnect()