#!/usr/bin/env python3
"""
Batch processor for validating HTML files and storing results in Neon database
"""

import os
import sys
import glob
import json
from pathlib import Path

# Add parent directory to path so we can import scripts modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.html_parser_with_validation import HuapalaHTMLParser
from scripts.database_validator import DatabaseValidator

class BatchProcessor:
    """Process multiple HTML files and store validation results"""
    
    def __init__(self, database_url: str = None):
        self.parser = HuapalaHTMLParser()
        self.db_validator = DatabaseValidator(database_url)
        
    def find_or_create_canonical_mele(self, parsed_song) -> str:
        """Find existing or create new canonical_mele record"""
        # This is a simplified version - you might want more sophisticated matching
        if not self.db_validator.conn:
            self.db_validator.connect()
        
        try:
            with self.db_validator.conn.cursor() as cursor:
                # Generate the canonical ID from title
                import re
                title = parsed_song.title.strip()
                # Remove newlines and extra spaces, convert to lowercase
                clean_title = re.sub(r'\s+', ' ', title.replace('\n', ' ')).strip()
                canonical_id = re.sub(r'[^a-zA-Z0-9\s]', '', clean_title.lower()).replace(' ', '_') + '_canonical'
                
                # Check if song already exists by ID
                cursor.execute("""
                    SELECT canonical_mele_id FROM canonical_mele 
                    WHERE canonical_mele_id = %s 
                    LIMIT 1
                """, (canonical_id,))
                
                result = cursor.fetchone()
                if result:
                    self.db_validator.logger.info(f"Found existing canonical_mele record: {canonical_id}")
                    return result[0]
                
                # Create new record with generated ID
                cursor.execute("""
                    INSERT INTO canonical_mele (
                        canonical_mele_id,
                        canonical_title_hawaiian, 
                        primary_composer
                    ) VALUES (%s, %s, %s)
                    RETURNING canonical_mele_id
                """, (
                    canonical_id,
                    clean_title,
                    parsed_song.composer.strip() if parsed_song.composer else ''
                ))
                
                song_id = cursor.fetchone()[0]
                self.db_validator.conn.commit()
                
                self.db_validator.logger.info(f"Created new canonical_mele record: {song_id}")
                return song_id
                
        except Exception as e:
            self.db_validator.conn.rollback()
            self.db_validator.logger.error(f"Failed to find/create canonical_mele: {e}")
            raise
    
    def process_file(self, file_path: str) -> bool:
        """Process a single HTML file"""
        try:
            self.db_validator.logger.info(f"Processing: {file_path}")
            
            # Parse the song
            parsed_song, validation_result = self.parser.parse_file(file_path)
            
            # Find or create canonical_mele record
            canonical_mele_id = self.find_or_create_canonical_mele(parsed_song)
            
            # Prepare validation data
            validation_data = self.parser._prepare_validation_data(parsed_song)
            validation_data['source_file'] = file_path
            
            # Store validation results
            self.db_validator.validate_and_store_song(validation_data, canonical_mele_id)
            
            self.db_validator.logger.info(f"Successfully processed: {file_path}")
            return True
            
        except Exception as e:
            self.db_validator.logger.error(f"Failed to process {file_path}: {e}")
            return False
    
    def process_directory(self, directory: str, pattern: str = "*.txt") -> dict:
        """Process all files in a directory matching the pattern"""
        
        # Start validation session
        session_name = f"batch_process_{Path(directory).name}_{self._timestamp()}"
        session_id = self.db_validator.start_validation_session(session_name)
        
        # Find all matching files
        search_pattern = os.path.join(directory, pattern)
        files = glob.glob(search_pattern)
        
        self.db_validator.logger.info(f"Found {len(files)} files to process in {directory}")
        
        # Process each file
        results = {
            'session_id': session_id,
            'session_name': session_name,
            'total_files': len(files),
            'successful': 0,
            'failed': 0,
            'failed_files': []
        }
        
        for file_path in files:
            if self.process_file(file_path):
                results['successful'] += 1
            else:
                results['failed'] += 1
                results['failed_files'].append(file_path)
        
        # Complete the session
        self.db_validator.complete_validation_session()
        
        # Generate summary
        self.db_validator.logger.info(f"Session completed: {results['successful']} successful, {results['failed']} failed")
        
        return results
    
    def _timestamp(self):
        """Get current timestamp for session naming"""
        from datetime import datetime
        return datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def cleanup(self):
        """Clean up database connections"""
        self.db_validator.disconnect()

def main():
    """Main entry point for batch processing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch process HTML files for Huapala database')
    parser.add_argument('directory', help='Directory containing HTML files to process')
    parser.add_argument('--pattern', default='*_CL.txt', help='File pattern to match (default: *_CL.txt)')
    parser.add_argument('--database-url', help='Database connection string (uses DATABASE_URL env var if not provided)')
    parser.add_argument('--dry-run', action='store_true', help='Parse files but don\'t store in database')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.directory):
        print(f"Error: Directory {args.directory} does not exist")
        return 1
    
    try:
        if args.dry_run:
            print("DRY RUN MODE - parsing files but not storing results")
            # Just use the regular parser for dry run
            parser = HuapalaHTMLParser()
            search_pattern = os.path.join(args.directory, args.pattern)
            files = glob.glob(search_pattern)
            
            print(f"Found {len(files)} files to process")
            successful = 0
            failed = 0
            
            for file_path in files:
                try:
                    parsed_song, validation_result = parser.parse_file(file_path)
                    print(f"✓ {file_path}: {parsed_song.title} (Quality: {validation_result.data_quality_score})")
                    successful += 1
                except Exception as e:
                    print(f"✗ {file_path}: {e}")
                    failed += 1
            
            print(f"\nDry run completed: {successful} successful, {failed} failed")
            
        else:
            # Real processing with database storage
            processor = BatchProcessor(args.database_url)
            
            try:
                results = processor.process_directory(args.directory, args.pattern)
                
                print(f"\nBatch processing completed:")
                print(f"Session ID: {results['session_id']}")
                print(f"Total files: {results['total_files']}")
                print(f"Successful: {results['successful']}")
                print(f"Failed: {results['failed']}")
                
                if results['failed_files']:
                    print(f"\nFailed files:")
                    for file_path in results['failed_files']:
                        print(f"  - {file_path}")
                
            finally:
                processor.cleanup()
        
        return 0
        
    except Exception as e:
        print(f"Error during batch processing: {e}")
        return 1

if __name__ == "__main__":
    exit(main())