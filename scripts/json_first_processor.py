#!/usr/bin/env python3
"""
JSON-First Song Processor

This creates a human-in-the-loop workflow:
1. Process HTML files → JSON files (reviewable/editable)
2. Manual review/editing step
3. Import reviewed JSON files → database

Usage:
  python3 scripts/json_first_processor.py parse data/cleaned_source_hml/    # HTML → JSON
  python3 scripts/json_first_processor.py import                           # JSON → Database
  python3 scripts/json_first_processor.py export                           # Database → JSON (for editing)
"""

import os
import sys
import json
import glob
import argparse
from pathlib import Path
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Add parent directory to path so we can import scripts modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.html_parser_with_validation import HuapalaHTMLParser
from scripts.raw_html_parser import RawHtmlParser

class JSONFirstProcessor:
    def __init__(self, database_url: str = None):
        self.parser = HuapalaHTMLParser()
        self.raw_parser = RawHtmlParser()
        self.database_url = database_url
        self.reviewed_dir = Path("data/reviewed_songs")
        self.reviewed_dir.mkdir(exist_ok=True)
        
    def parse_to_json(self, directory: str, pattern: str = "*.txt") -> dict:
        """Parse HTML files and create JSON files for manual review"""
        
        search_pattern = os.path.join(directory, pattern)
        files = glob.glob(search_pattern)
        
        results = {"processed": [], "failed": [], "timestamp": datetime.now().isoformat()}
        
        print(f"📁 Found {len(files)} files to process in {directory}")
        
        for file_path in files:
            try:
                print(f"📥 Processing: {file_path}")
                
                # Determine which parser to use based on file content/location
                if self._is_raw_html_file(file_path):
                    print(f"   Using raw HTML parser")
                    parsed_song, validation_result = self.raw_parser.parse_file(file_path)
                else:
                    print(f"   Using cleaned HTML parser")
                    parsed_song, validation_result = self.parser.parse_file(file_path)
                
                # Generate canonical ID
                clean_title = self._clean_title(parsed_song.title)
                canonical_id = self._generate_canonical_id(clean_title)
                
                # Create the reviewable JSON structure
                song_data = {
                    "canonical_mele_id": canonical_id,
                    "canonical_title_hawaiian": clean_title,
                    "canonical_title_english": getattr(parsed_song, 'english_title', '') or "",
                    "primary_composer": parsed_song.composer.strip() if parsed_song.composer else "",
                    "translator": parsed_song.translator.strip() if parsed_song.translator else "",
                    "source_file": file_path,
                    "processing_metadata": {
                        "original_file": file_path,
                        "processed_at": datetime.now().isoformat(),
                        "parsing_quality_score": getattr(validation_result, 'quality_score', 0) if validation_result else 0,
                        "total_sections": len(parsed_song.sections),
                        "total_lines": sum(len(section.lines) for section in parsed_song.sections)
                    },
                    "verses": []
                }
                
                # Process each section with editable structure
                for i, section in enumerate(parsed_song.sections):
                    verse_data = {
                        "id": f"{section.section_type[0]}{section.number}" if hasattr(section, 'number') else f"{section.section_type[0]}{i+1}",
                        "type": section.section_type,
                        "number": getattr(section, 'number', i + 1),
                        "order": i + 1,
                        "label": self._generate_verse_label(section.section_type, getattr(section, 'number', i + 1)),
                        "lines": []
                    }
                    
                    # Add each line as an editable object
                    for j, line in enumerate(section.lines):
                        line_data = {
                            "id": f"{verse_data['id']}.{j+1}",
                            "line_number": j + 1,
                            "hawaiian_text": line.hawaiian_text.strip() if line.hawaiian_text else "",
                            "english_text": line.english_text.strip() if line.english_text else "",
                            "is_bilingual": bool(line.hawaiian_text and line.english_text)
                        }
                        verse_data["lines"].append(line_data)
                    
                    song_data["verses"].append(verse_data)
                
                # Save to JSON file for review
                json_filename = f"{canonical_id}.json"
                json_path = self.reviewed_dir / json_filename
                
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(song_data, f, indent=2, ensure_ascii=False)
                
                results["processed"].append({
                    "file": file_path,
                    "json_path": str(json_path),
                    "canonical_id": canonical_id,
                    "sections": len(parsed_song.sections),
                    "lines": sum(len(section.lines) for section in parsed_song.sections)
                })
                
                print(f"   ✅ Created reviewable JSON: {json_path}")
                
            except Exception as e:
                results["failed"].append({"file": file_path, "error": str(e)})
                print(f"   ❌ Failed: {e}")
        
        # Save processing report
        report_path = self.reviewed_dir / "processing_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Processing complete:")
        print(f"   ✅ Successfully processed: {len(results['processed'])} files")
        print(f"   ❌ Failed: {len(results['failed'])} files")
        print(f"   📊 Report saved to: {report_path}")
        print(f"\n📝 Review and edit JSON files in: {self.reviewed_dir}")
        print(f"💡 When ready, run: python3 {__file__} import")
        
        return results
    
    def import_from_json(self) -> dict:
        """Import reviewed JSON files to database"""
        
        if not self.database_url:
            raise ValueError("Database URL required for import. Set DATABASE_URL environment variable.")
        
        json_files = list(self.reviewed_dir.glob("*.json"))
        # Exclude report files
        json_files = [f for f in json_files if not f.name.endswith("_report.json")]
        
        if not json_files:
            print(f"❌ No JSON files found in {self.reviewed_dir}")
            return {"imported": [], "failed": []}
        
        conn = psycopg2.connect(self.database_url)
        results = {"imported": [], "failed": [], "timestamp": datetime.now().isoformat()}
        
        print(f"📁 Found {len(json_files)} JSON files to import")
        
        for json_file in json_files:
            try:
                print(f"📥 Importing: {json_file}")
                
                with open(json_file, 'r', encoding='utf-8') as f:
                    song_data = json.load(f)
                
                # Import to database
                self._import_song_to_database(conn, song_data)
                
                # Calculate total lines safely
                total_lines = 0
                for verse in song_data["verses"]:
                    if "lines" in verse and isinstance(verse["lines"], list):
                        total_lines += len(verse["lines"])
                    elif "hawaiian_lines" in verse:
                        h_lines = verse["hawaiian_lines"]
                        if isinstance(h_lines, list):
                            total_lines += len(h_lines)
                        elif h_lines:
                            total_lines += 1
                
                results["imported"].append({
                    "file": str(json_file),
                    "canonical_id": song_data["canonical_mele_id"],
                    "sections": len(song_data["verses"]),
                    "total_lines": total_lines
                })
                
                print(f"   ✅ Imported: {song_data['canonical_mele_id']}")
                
            except Exception as e:
                results["failed"].append({"file": str(json_file), "error": str(e)})
                print(f"   ❌ Failed: {e}")
                conn.rollback()
        
        conn.close()
        
        # Save import report
        import_report_path = self.reviewed_dir / "import_report.json"
        with open(import_report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Import complete:")
        print(f"   ✅ Successfully imported: {len(results['imported'])} songs")
        print(f"   ❌ Failed: {len(results['failed'])} songs")
        print(f"   📊 Report saved to: {import_report_path}")
        
        return results
    
    def export_from_database(self) -> dict:
        """Export current database songs to JSON for editing"""
        
        if not self.database_url:
            raise ValueError("Database URL required for export. Set DATABASE_URL environment variable.")
        
        conn = psycopg2.connect(self.database_url)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all songs with their verses
        query = """
        SELECT 
            cm.canonical_mele_id,
            cm.canonical_title_hawaiian,
            cm.canonical_title_english,
            cm.primary_composer,
            cm.primary_lyricist,
            ms.composer,
            ms.translator,
            ms.source_file,
            ms.verses_json
        FROM canonical_mele cm
        LEFT JOIN mele_sources ms ON cm.canonical_mele_id = ms.canonical_mele_id
        ORDER BY cm.canonical_title_hawaiian
        """
        
        cur.execute(query)
        rows = cur.fetchall()
        
        results = {"exported": [], "failed": [], "timestamp": datetime.now().isoformat()}
        
        print(f"📁 Found {len(rows)} songs in database")
        
        for row in rows:
            try:
                song = dict(row)
                canonical_id = song['canonical_mele_id']
                
                # Parse verses JSON
                verses = []
                if song['verses_json']:
                    verses = json.loads(song['verses_json'])
                
                # Create editable JSON structure
                song_data = {
                    "canonical_mele_id": canonical_id,
                    "canonical_title_hawaiian": song['canonical_title_hawaiian'] or "",
                    "canonical_title_english": song['canonical_title_english'] or "",
                    "primary_composer": song['primary_composer'] or song['composer'] or "",
                    "translator": song['translator'] or "",
                    "source_file": song['source_file'] or "",
                    "processing_metadata": {
                        "exported_at": datetime.now().isoformat(),
                        "source": "database_export",
                        "total_sections": len(verses) if verses else 0,
                        "total_lines": sum(len(verse.get("lines", [])) for verse in verses) if verses else 0
                    },
                    "verses": verses
                }
                
                # Save to JSON file
                json_filename = f"{canonical_id}.json"
                json_path = self.reviewed_dir / json_filename
                
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(song_data, f, indent=2, ensure_ascii=False)
                
                results["exported"].append({
                    "canonical_id": canonical_id,
                    "json_path": str(json_path),
                    "sections": len(verses) if verses else 0
                })
                
                print(f"   ✅ Exported: {canonical_id}")
                
            except Exception as e:
                results["failed"].append({"canonical_id": song.get('canonical_mele_id', 'unknown'), "error": str(e)})
                print(f"   ❌ Failed: {e}")
        
        conn.close()
        
        # Save export report
        export_report_path = self.reviewed_dir / "export_report.json"
        with open(export_report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Export complete:")
        print(f"   ✅ Successfully exported: {len(results['exported'])} songs")
        print(f"   ❌ Failed: {len(results['failed'])} songs")
        print(f"   📊 Report saved to: {export_report_path}")
        print(f"\n📝 Edit JSON files in: {self.reviewed_dir}")
        print(f"💡 When ready, run: python3 {__file__} import")
        
        return results
    
    def _import_song_to_database(self, conn, song_data):
        """Import a single song from JSON to database"""
        
        with conn.cursor() as cursor:
            canonical_id = song_data["canonical_mele_id"]
            
            # Upsert canonical_mele
            cursor.execute("""
                INSERT INTO canonical_mele (
                    canonical_mele_id,
                    canonical_title_hawaiian,
                    canonical_title_english,
                    primary_composer,
                    primary_lyricist
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (canonical_mele_id) DO UPDATE SET
                    canonical_title_hawaiian = EXCLUDED.canonical_title_hawaiian,
                    canonical_title_english = EXCLUDED.canonical_title_english,
                    primary_composer = EXCLUDED.primary_composer,
                    primary_lyricist = EXCLUDED.primary_lyricist,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                canonical_id,
                song_data["canonical_title_hawaiian"],
                song_data.get("canonical_title_english", ""),
                song_data["primary_composer"],
                song_data.get("primary_lyricist", "")
            ))
            
            # Update or insert mele_sources with verses
            # First try to update existing record
            cursor.execute("""
                UPDATE mele_sources SET
                    composer = %s,
                    translator = %s,
                    source_file = %s,
                    verses_json = %s,
                    processing_status = %s,
                    extraction_date = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE canonical_mele_id = %s
            """, (
                song_data["primary_composer"],
                song_data.get("translator", ""),
                song_data.get("source_file", ""),
                json.dumps({
                    "verses": self._normalize_verses_format(song_data["verses"]),
                    "processing_metadata": {}
                }, ensure_ascii=False),
                "reviewed_and_imported",
                datetime.now(),
                canonical_id
            ))
            
            # If no rows were updated, insert new record
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO mele_sources (
                        id,
                        canonical_mele_id,
                        source_specific_title,
                        composer,
                        translator,
                        source_file,
                        verses_json,
                        song_type,
                        structure_type,
                        processing_status,
                        extraction_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    canonical_id + "_source",  # Create unique ID
                    canonical_id,
                    song_data.get("canonical_title_hawaiian", ""),  # source_specific_title
                    song_data["primary_composer"],
                    song_data.get("translator", ""),
                    song_data.get("source_file", ""),
                    json.dumps({
                    "verses": self._normalize_verses_format(song_data["verses"]),
                    "processing_metadata": {}
                }, ensure_ascii=False),
                    "mele",  # song_type - all current songs are mele
                    self._detect_structure_type(song_data["verses"]),  # structure_type
                    "reviewed_and_imported",
                    datetime.now()
                ))
            
            conn.commit()
    
    def _clean_title(self, title: str) -> str:
        """Clean title for storage"""
        import re
        return re.sub(r'\s+', ' ', title.replace('\n', ' ')).strip()
    
    def _generate_canonical_id(self, title: str) -> str:
        """Generate canonical ID from title with consistent special character handling"""
        import re
        import unicodedata
        
        # First normalize unicode characters (ū → u, ī → i, etc.)
        normalized = unicodedata.normalize('NFKD', title)
        
        # Remove accents/diacritics 
        ascii_title = ''.join(c for c in normalized if not unicodedata.combining(c))
        
        # Convert to lowercase and remove all non-alphanumeric except spaces
        clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', ascii_title.lower())
        
        # Replace multiple spaces with single space, then replace spaces with underscores
        clean_title = re.sub(r'\s+', ' ', clean_title).strip().replace(' ', '_')
        
        return f"{clean_title}_canonical"
    
    def _is_raw_html_file(self, file_path: str) -> bool:
        """Determine if a file is raw HTML (not cleaned)"""
        # Check if the file is in source_html directory (raw files)
        path_obj = Path(file_path)
        if 'source_html' in path_obj.parts:
            return True
        
        # Check file content for HTML tags that indicate raw HTML
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)  # Read first 500 chars
                # Look for DOCTYPE, html tags, or other raw HTML indicators
                raw_indicators = ['<!DOCTYPE', '<html>', '<head>', '<body>', '<title>']
                return any(indicator in content for indicator in raw_indicators)
        except:
            return False
    
    def _generate_verse_label(self, section_type: str, number: int) -> str:
        """Generate human-readable verse label"""
        if section_type in ['chorus', 'hui']:
            return "Hui:"
        elif section_type == 'verse':
            return f"Verse {number}:"
        else:
            return f"{section_type.title()} {number}:"
    
    def _detect_structure_type(self, verses: list) -> str:
        """Detect song structure type based on verse patterns"""
        if not verses:
            return "unknown"
            
        # Count verses and choruses
        verse_count = len([v for v in verses if v.get('type') == 'verse'])
        chorus_count = len([v for v in verses if v.get('type') == 'chorus'])
        
        # Analyze verse line patterns
        verse_line_counts = []
        has_hui = chorus_count > 0
        
        for verse in verses:
            if verse.get('type') == 'verse':
                lines = verse.get('lines', [])
                line_count = len(lines)
                verse_line_counts.append(line_count)
        
        # Determine structure based on patterns
        if has_hui:
            return 'verse-chorus'
        elif verse_line_counts:
            if len(verse_line_counts) >= 2:  # Need at least 2 verses for strophic
                if all(count == 4 for count in verse_line_counts):
                    return '4-line-strophic'
                elif all(count == 2 for count in verse_line_counts):
                    return '2-line-strophic'
                elif len(set(verse_line_counts)) == 1:  # All same length
                    return 'other'  # Regular but not 2 or 4 lines
                else:
                    return 'through-composed'  # Irregular patterns
            else:
                return 'other'  # Single verse or unclear pattern
        else:
            return 'unknown'
    
    def _normalize_verses_format(self, verses: list) -> list:
        """Convert verses to the new format with lines array"""
        normalized = []
        
        for verse in verses:
            # If it already has the new format with lines array, use as-is
            if "lines" in verse and isinstance(verse["lines"], list):
                normalized.append(verse)
                continue
            
            # Convert old format (hawaiian_lines/english_lines) to new format
            normalized_verse = {
                "id": verse.get("id", f"v{len(normalized)+1}"),
                "type": verse.get("type", "verse"),
                "number": verse.get("number", len(normalized)+1),
                "order": verse.get("order", len(normalized)+1),
                "lines": []
            }
            
            # Add label if present
            if "label" in verse:
                normalized_verse["label"] = verse["label"]
            
            # Convert line-by-line data
            if "hawaiian_lines" in verse and "english_lines" in verse:
                hawaiian_lines = verse["hawaiian_lines"] or []
                english_lines = verse["english_lines"] or []
                
                # Handle single strings vs arrays
                if isinstance(hawaiian_lines, str):
                    hawaiian_lines = [hawaiian_lines]
                if isinstance(english_lines, str):
                    english_lines = [english_lines]
                
                max_lines = max(len(hawaiian_lines), len(english_lines))
                
                for i in range(max_lines):
                    h_text = hawaiian_lines[i] if i < len(hawaiian_lines) else ""
                    e_text = english_lines[i] if i < len(english_lines) else ""
                    
                    line_obj = {
                        "id": f"{normalized_verse['id']}.{i+1}",
                        "line_number": i + 1,
                        "hawaiian_text": h_text.strip() if h_text else "",
                        "english_text": e_text.strip() if e_text else "",
                        "is_bilingual": bool(h_text and e_text)
                    }
                    normalized_verse["lines"].append(line_obj)
            
            # Fallback: use hawaiian_text/english_text if available
            elif "hawaiian_text" in verse or "english_text" in verse:
                h_text = verse.get("hawaiian_text", "")
                e_text = verse.get("english_text", "")
                
                line_obj = {
                    "id": f"{normalized_verse['id']}.1",
                    "line_number": 1,
                    "hawaiian_text": h_text.strip() if h_text else "",
                    "english_text": e_text.strip() if e_text else "",
                    "is_bilingual": bool(h_text and e_text)
                }
                normalized_verse["lines"].append(line_obj)
            
            normalized.append(normalized_verse)
        
        return normalized

def main():
    parser = argparse.ArgumentParser(description='JSON-First Song Processor')
    parser.add_argument('command', choices=['parse', 'import', 'export'], 
                       help='Command to execute')
    parser.add_argument('directory', nargs='?', 
                       help='Directory to parse (for parse command)')
    parser.add_argument('--pattern', default='*.txt',
                       help='File pattern to match (default: *.txt)')
    parser.add_argument('--database-url', 
                       help='Database URL (or set DATABASE_URL env var)')
    
    args = parser.parse_args()
    
    # Get database URL from args or environment
    database_url = args.database_url or os.getenv('DATABASE_URL')
    
    processor = JSONFirstProcessor(database_url)
    
    try:
        if args.command == 'parse':
            if not args.directory:
                print("❌ Directory required for parse command")
                return
            processor.parse_to_json(args.directory, args.pattern)
            
        elif args.command == 'import':
            processor.import_from_json()
            
        elif args.command == 'export':
            processor.export_from_database()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())