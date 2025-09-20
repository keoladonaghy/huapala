#!/usr/bin/env python3
"""
Import Hawaiian Songbook Data to PostgreSQL

Imports the tab-delimited songbook entries file into the songbook_entries table.
Handles data cleaning, type conversion, and error reporting.
"""

import os
import sys
import csv
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path so we can import scripts modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SongbookDataImporter:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            # Construct from individual components like main.py
            self.database_url = self._construct_database_url()
        
        self.imported_count = 0
        self.failed_count = 0
        self.errors = []

    def _construct_database_url(self) -> str:
        """Construct database URL from environment variables like main.py"""
        host = os.getenv('PGHOST', 'ep-young-silence-ad9wue88-pooler.c-2.us-east-1.aws.neon.tech')
        database = os.getenv('PGDATABASE', 'neondb')
        user = os.getenv('PGUSER', 'neondb_owner')
        password = os.getenv('PGPASSWORD', 'npg_Ic2Qq1ErOykl')  # Use same fallback as main.py
        port = os.getenv('PGPORT', '5432')
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    def clean_integer_field(self, value: str) -> int:
        """Convert string to integer, handling various formats"""
        if not value or value.strip() == '':
            return None
        
        # Remove any non-digit characters except for ranges
        cleaned = value.strip()
        
        # Handle ranges like "12-14" - take first number
        if '-' in cleaned:
            cleaned = cleaned.split('-')[0]
        
        # Handle other separators
        if '/' in cleaned:
            cleaned = cleaned.split('/')[0]
        
        try:
            return int(cleaned)
        except ValueError:
            return None

    def clean_timestamp_field(self, value: str) -> datetime:
        """Convert timestamp string to datetime object"""
        if not value or value.strip() == '':
            return None
        
        try:
            # Parse format: "11/8/2015 15:18:26"
            return datetime.strptime(value.strip(), "%m/%d/%Y %H:%M:%S")
        except ValueError:
            try:
                # Try alternative format
                return datetime.strptime(value.strip(), "%m/%d/%Y")
            except ValueError:
                return None

    def clean_diacritics_field(self, value: str) -> str:
        """Normalize diacritics field to allowed values"""
        if not value or value.strip() == '':
            return 'Unknown'
        
        cleaned = value.strip().lower()
        if cleaned in ['yes', 'y', 'true']:
            return 'Yes'
        elif cleaned in ['no', 'n', 'false']:
            return 'No'
        elif cleaned in ['inconsistent', 'mixed', 'partial']:
            return 'Inconsistent'
        else:
            return 'Unknown'

    def clean_text_field(self, value: str) -> str:
        """Clean text field, handling None and empty strings"""
        if not value:
            return None
        
        cleaned = value.strip()
        return cleaned if cleaned else None

    def process_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Process a single row of data"""
        return {
            'timestamp': self.clean_timestamp_field(row.get('timestamp')),
            'printed_song_title': self.clean_text_field(row.get('printed_song_title')),
            'eng_title_transl': self.clean_text_field(row.get('eng_title_transl')),
            'modern_song_title': self.clean_text_field(row.get('modern_song_title')),
            'scripped_song_title': self.clean_text_field(row.get('scripped_song_title')),
            'song_title': self.clean_text_field(row.get('Song Title')),
            'songbook_name': self.clean_text_field(row.get('songbook_name')),
            'page': self.clean_integer_field(row.get('page')),
            'pub_year': self.clean_integer_field(row.get('pub_year')),
            'diacritics': self.clean_diacritics_field(row.get('diacritics')),
            'composer': self.clean_text_field(row.get('Composer')),
            'additional_information': self.clean_text_field(row.get('Additional Information')),
            'email_address': self.clean_text_field(row.get('Email Address'))
            # Note: canonical_mele_id will be NULL initially - to be linked later
        }

    def create_table(self, conn):
        """Create the songbook_entries table"""
        print("🏗️  Creating songbook_entries table...")
        
        with open('scripts/create_songbook_entries_table.sql', 'r') as f:
            schema_sql = f.read()
        
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.commit()
        print("   ✅ Table created successfully")

    def import_data(self, file_path: str):
        """Import data from tab-delimited file"""
        print(f"📥 Starting import from: {file_path}")
        
        # Connect to database
        conn = psycopg2.connect(self.database_url)
        
        try:
            # Create table first
            self.create_table(conn)
            
            # Read and process data - try different encodings
            encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            file_content = None
            
            for encoding in encodings_to_try:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        file_content = f.read()
                    print(f"   📖 Successfully read file with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            
            if file_content is None:
                raise ValueError("Could not decode file with any supported encoding")
            
            # Process the content
            from io import StringIO
            reader = csv.DictReader(StringIO(file_content), delimiter='\t')
            
            batch_data = []
            batch_size = 100
            
            for row_num, row in enumerate(reader, 2):  # Start at 2 (header is line 1)
                try:
                    processed_row = self.process_row(row)
                    batch_data.append(processed_row)
                    
                    # Insert batch when it reaches batch_size
                    if len(batch_data) >= batch_size:
                        self._insert_batch(conn, batch_data)
                        batch_data = []
                    
                except Exception as e:
                    self.failed_count += 1
                    error_msg = f"Row {row_num}: {str(e)}"
                    self.errors.append(error_msg)
                    print(f"   ❌ {error_msg}")
            
            # Insert remaining records
            if batch_data:
                self._insert_batch(conn, batch_data)
            
            conn.commit()
            print(f"\n📊 Import Summary:")
            print(f"   ✅ Successfully imported: {self.imported_count} records")
            print(f"   ❌ Failed: {self.failed_count} records")
            
            if self.errors:
                print(f"\n⚠️  Errors encountered:")
                for error in self.errors[:10]:  # Show first 10 errors
                    print(f"   • {error}")
                if len(self.errors) > 10:
                    print(f"   ... and {len(self.errors) - 10} more errors")
        
        except Exception as e:
            conn.rollback()
            print(f"❌ Import failed: {e}")
            raise
        
        finally:
            conn.close()

    def _insert_batch(self, conn, batch_data: List[Dict[str, Any]]):
        """Insert a batch of records"""
        if not batch_data:
            return
        
        insert_sql = """
        INSERT INTO songbook_entries (
            timestamp, printed_song_title, eng_title_transl, modern_song_title,
            scripped_song_title, song_title, songbook_name, page, pub_year,
            diacritics, composer, additional_information, email_address
        ) VALUES %s
        """
        
        # Convert batch data to tuples
        values = []
        for row in batch_data:
            values.append((
                row['timestamp'], row['printed_song_title'], row['eng_title_transl'],
                row['modern_song_title'], row['scripped_song_title'], row['song_title'],
                row['songbook_name'], row['page'], row['pub_year'], row['diacritics'],
                row['composer'], row['additional_information'], row['email_address']
            ))
        
        with conn.cursor() as cur:
            execute_values(cur, insert_sql, values, template=None, page_size=100)
        
        self.imported_count += len(batch_data)
        print(f"   📝 Inserted batch of {len(batch_data)} records (total: {self.imported_count})")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Import Hawaiian Songbook Data')
    parser.add_argument('file_path', nargs='?', 
                       default='data/songbooks/Hawaiian_Songbook_Songs_updated.txt',
                       help='Path to tab-delimited songbook data file')
    parser.add_argument('--database-url', 
                       help='Database URL (or set PGPASSWORD env var)')
    
    args = parser.parse_args()
    
    try:
        importer = SongbookDataImporter(args.database_url)
        importer.import_data(args.file_path)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())