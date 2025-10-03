#!/usr/bin/env python3
"""
Data Integrity Validation Script

This script validates the integrity of the Huapala song data across all formats:
1. Source JSON files in /data/extracted_json/
2. Database records in mele_sources.verses_json
3. Web export data in public/songs-data.json

Checks for:
- Proper JSON format and structure
- Required fields presence
- Data consistency between sources
- Corruption patterns
- Missing or orphaned records

Can be run manually or scheduled as a cron job for periodic validation.
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple
from sqlalchemy import create_engine, text

# Add parent directory to path to import auth
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import get_database_url

# Database connection
DB_URL = get_database_url()

class DataValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.stats = {
            'source_files': 0,
            'db_records': 0,
            'web_songs': 0,
            'corrupted_formats': 0,
            'missing_fields': 0,
            'orphaned_records': 0
        }
        
    def log_error(self, category: str, item: str, message: str):
        """Log a validation error"""
        self.errors.append(f"[{category}] {item}: {message}")
        
    def log_warning(self, category: str, item: str, message: str):
        """Log a validation warning"""
        self.warnings.append(f"[{category}] {item}: {message}")
        
    def validate_verses_structure(self, verses_data: Any, source: str) -> bool:
        """Validate the verses JSON structure"""
        if isinstance(verses_data, str):
            try:
                parsed = json.loads(verses_data)
            except json.JSONDecodeError as e:
                self.log_error("JSON", source, f"Invalid JSON: {e}")
                return False
        else:
            parsed = verses_data
            
        # Check for correct wrapper format
        if not isinstance(parsed, dict):
            self.log_error("STRUCTURE", source, "verses_json should be a dict")
            self.stats['corrupted_formats'] += 1
            return False
            
        if 'verses' not in parsed:
            self.log_error("STRUCTURE", source, "Missing 'verses' key in wrapper")
            self.stats['corrupted_formats'] += 1
            return False
            
        if 'processing_metadata' not in parsed:
            self.log_warning("STRUCTURE", source, "Missing 'processing_metadata' key")
            
        verses = parsed['verses']
        if not isinstance(verses, list):
            self.log_error("STRUCTURE", source, "'verses' should be a list")
            return False
            
        # Validate individual verses
        for i, verse in enumerate(verses):
            if not isinstance(verse, dict):
                self.log_error("VERSE", source, f"Verse {i+1} is not a dict")
                continue
                
            required_fields = ['id', 'type', 'number', 'order']
            for field in required_fields:
                if field not in verse:
                    self.log_error("VERSE", source, f"Verse {i+1} missing required field '{field}'")
                    self.stats['missing_fields'] += 1
                    
            # Validate lines structure if present
            if 'lines' in verse:
                if not isinstance(verse['lines'], list):
                    self.log_error("LINES", source, f"Verse {i+1} 'lines' should be a list")
                    continue
                    
                for j, line in enumerate(verse['lines']):
                    if not isinstance(line, dict):
                        self.log_error("LINE", source, f"Verse {i+1}, Line {j+1} is not a dict")
                        continue
                        
                    line_required = ['id', 'line_number', 'hawaiian_text', 'english_text', 'is_bilingual']
                    for field in line_required:
                        if field not in line:
                            self.log_error("LINE", source, f"Verse {i+1}, Line {j+1} missing '{field}'")
                            self.stats['missing_fields'] += 1
                            
        return True
        
    def validate_source_files(self) -> Dict[str, Any]:
        """Validate JSON files in /data/extracted_json/"""
        source_dir = Path("data/extracted_json")
        source_files = {}
        
        if not source_dir.exists():
            self.log_error("FILESYSTEM", "source_dir", f"Directory {source_dir} does not exist")
            return source_files
            
        for json_file in source_dir.glob("*.json"):
            if json_file.name in ['extraction_summary.json']:
                continue  # Skip summary files
                
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                self.stats['source_files'] += 1
                song_id = data.get('id', json_file.stem)
                source_files[song_id] = {
                    'file': str(json_file),
                    'data': data
                }
                
                # Validate basic structure
                required_top_level = ['id', 'title', 'content']
                for field in required_top_level:
                    if field not in data:
                        self.log_error("SOURCE", song_id, f"Missing top-level field '{field}'")
                        self.stats['missing_fields'] += 1
                        
                # Validate verses if present
                if 'content' in data and 'verses' in data['content']:
                    # Note: Source files have the old format, this is expected
                    verses = data['content']['verses']
                    if not isinstance(verses, list):
                        self.log_error("SOURCE", song_id, "content.verses should be a list")
                        
            except json.JSONDecodeError as e:
                self.log_error("SOURCE", str(json_file), f"Invalid JSON: {e}")
            except Exception as e:
                self.log_error("SOURCE", str(json_file), f"Error reading file: {e}")
                
        return source_files
        
    def validate_database_records(self) -> Dict[str, Any]:
        """Validate database mele_sources records"""
        db_records = {}
        
        try:
            engine = create_engine(DB_URL)
            with engine.connect() as conn:
                query = text("""
                SELECT ms.canonical_mele_id, ms.verses_json, 
                       cm.canonical_title_hawaiian, cm.canonical_title_english,
                       cm.primary_composer, ms.updated_at
                FROM mele_sources ms
                JOIN canonical_mele cm ON ms.canonical_mele_id = cm.canonical_mele_id
                WHERE ms.verses_json IS NOT NULL
                ORDER BY ms.canonical_mele_id
                """)
                
                results = conn.execute(query).fetchall()
                
                for row in results:
                    song_id = row[0]
                    verses_json = row[1]
                    
                    self.stats['db_records'] += 1
                    db_records[song_id] = {
                        'verses_json': verses_json,
                        'title_hawaiian': row[2],
                        'title_english': row[3],
                        'composer': row[4],
                        'updated_at': row[5]
                    }
                    
                    # Validate verses structure
                    self.validate_verses_structure(verses_json, f"DB:{song_id}")
                    
        except Exception as e:
            self.log_error("DATABASE", "connection", f"Error connecting to database: {e}")
            
        return db_records
        
    def validate_web_export(self) -> Dict[str, Any]:
        """Validate public/songs-data.json export"""
        web_songs = {}
        web_file = Path("public/songs-data.json")
        
        if not web_file.exists():
            self.log_warning("WEB", "export", f"Web export file {web_file} does not exist")
            return web_songs
            
        try:
            with open(web_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, list):
                self.log_error("WEB", "export", "Web export should be a list of songs")
                return web_songs
                
            for song in data:
                if not isinstance(song, dict):
                    self.log_error("WEB", "export", "Song entry should be a dict")
                    continue
                    
                song_id = song.get('canonical_mele_id', 'unknown')
                self.stats['web_songs'] += 1
                web_songs[song_id] = song
                
                # Validate required fields for web export
                web_required = ['canonical_mele_id', 'canonical_title_hawaiian', 'verses']
                for field in web_required:
                    if field not in song:
                        self.log_error("WEB", song_id, f"Missing required field '{field}'")
                        self.stats['missing_fields'] += 1
                        
                # Validate verses structure in web export
                if 'verses' in song:
                    if not isinstance(song['verses'], list):
                        self.log_error("WEB", song_id, "'verses' should be a list")
                        
        except json.JSONDecodeError as e:
            self.log_error("WEB", "export", f"Invalid JSON: {e}")
        except Exception as e:
            self.log_error("WEB", "export", f"Error reading web export: {e}")
            
        return web_songs
        
    def check_consistency(self, source_files: Dict, db_records: Dict, web_songs: Dict):
        """Check consistency between different data sources"""
        all_ids = set(source_files.keys()) | set(db_records.keys()) | set(web_songs.keys())
        
        for song_id in all_ids:
            in_source = song_id in source_files
            in_db = song_id in db_records
            in_web = song_id in web_songs
            
            if in_source and not in_db:
                self.log_warning("CONSISTENCY", song_id, "In source files but not in database")
                self.stats['orphaned_records'] += 1
                
            if in_db and not in_web:
                self.log_warning("CONSISTENCY", song_id, "In database but not in web export")
                
            if in_web and not in_db:
                self.log_error("CONSISTENCY", song_id, "In web export but not in database")
                
    def generate_report(self) -> str:
        """Generate a comprehensive validation report"""
        report = []
        report.append("=" * 80)
        report.append("HUAPALA DATA INTEGRITY VALIDATION REPORT")
        report.append(f"Generated: {datetime.now()}")
        report.append("=" * 80)
        report.append("")
        
        # Statistics
        report.append("STATISTICS:")
        report.append(f"  Source JSON files: {self.stats['source_files']}")
        report.append(f"  Database records: {self.stats['db_records']}")
        report.append(f"  Web export songs: {self.stats['web_songs']}")
        report.append(f"  Corrupted formats: {self.stats['corrupted_formats']}")
        report.append(f"  Missing fields: {self.stats['missing_fields']}")
        report.append(f"  Orphaned records: {self.stats['orphaned_records']}")
        report.append("")
        
        # Overall status
        total_issues = len(self.errors) + len(self.warnings)
        if total_issues == 0:
            report.append("✅ STATUS: ALL VALIDATIONS PASSED")
        elif len(self.errors) == 0:
            report.append(f"⚠️  STATUS: {len(self.warnings)} WARNINGS (no critical errors)")
        else:
            report.append(f"❌ STATUS: {len(self.errors)} ERRORS, {len(self.warnings)} WARNINGS")
        report.append("")
        
        # Errors
        if self.errors:
            report.append("ERRORS:")
            for error in self.errors:
                report.append(f"  ❌ {error}")
            report.append("")
            
        # Warnings
        if self.warnings:
            report.append("WARNINGS:")
            for warning in self.warnings:
                report.append(f"  ⚠️  {warning}")
            report.append("")
            
        report.append("=" * 80)
        return "\n".join(report)
        
    def run_validation(self) -> bool:
        """Run complete validation and return True if no errors"""
        print("Starting data integrity validation...")
        
        # Validate each data source
        source_files = self.validate_source_files()
        db_records = self.validate_database_records()
        web_songs = self.validate_web_export()
        
        # Check consistency between sources
        self.check_consistency(source_files, db_records, web_songs)
        
        # Generate and display report
        report = self.generate_report()
        print(report)
        
        # Save report to file
        report_file = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\nReport saved to: {report_file}")
        
        return len(self.errors) == 0

def main():
    """Main function"""
    if 'PGPASSWORD' not in os.environ:
        print("Error: PGPASSWORD environment variable not set")
        sys.exit(1)
        
    validator = DataValidator()
    success = validator.run_validation()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()