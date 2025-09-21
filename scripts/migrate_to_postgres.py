#!/usr/bin/env python3
"""
Huapala Mele Migration Script for PostgreSQL

Migrates JSON mele data to the new PostgreSQL database structure.
Handles data transformation, URL extraction, and generates reports for manual curation.

Usage: python migrate_to_postgres.py [options]
"""

import json
import os
import re
import sys
import csv
from datetime import datetime
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values
import argparse

# Database configuration
DB_CONFIG = {
    'host': 'ep-young-silence-ad9wue88-pooler.c-2.us-east-1.aws.neon.tech',
    'database': 'neondb',
    'user': 'neondb_owner',
    'password': os.getenv('PGPASSWORD'),
    'port': 5432,
    'sslmode': 'require'
}

def load_config():
    """Load database configuration from environment or config file"""
    config = DB_CONFIG.copy()
    
    # Override with environment variables if present
    config['host'] = os.getenv('DB_HOST', config['host'])
    config['database'] = os.getenv('DB_NAME', config['database'])
    config['user'] = os.getenv('DB_USER', config['user'])
    config['password'] = os.getenv('DB_PASSWORD', config['password'])
    config['port'] = int(os.getenv('DB_PORT', config['port']))
    
    return config

def extract_youtube_urls(text):
    """Extract YouTube URLs from text content"""
    if not text:
        return []
    
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'https?://youtu\.be/[\w-]+',
        r'http://www\.youtube\.com/watch\?v=[\w-]+'
    ]
    
    urls = []
    for pattern in youtube_patterns:
        matches = re.findall(pattern, text)
        urls.extend(matches)
    
    return list(set(urls))  # Remove duplicates

def clean_text_for_db(text):
    """Clean text content for database insertion"""
    if not text:
        return ""
    
    # Remove YouTube URLs from text content
    youtube_patterns = [
        r'Listen to [^h]*https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'https?://youtu\.be/[\w-]+',
        r'http://www\.youtube\.com/watch\?v=[\w-]+'
    ]
    
    cleaned = text
    for pattern in youtube_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Clean up extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned

def normalize_id(title):
    """Create normalized ID from title (same as original extract_mele.py)"""
    if not title:
        return "unknown"
    
    # Remove diacriticals for ID
    id_text = title.lower()
    id_text = re.sub(r'[ʻ''`]', '', id_text)  # Remove okina variants
    id_text = re.sub(r'[āăâ]', 'a', id_text)
    id_text = re.sub(r'[ēĕê]', 'e', id_text)
    id_text = re.sub(r'[īĭî]', 'i', id_text)
    id_text = re.sub(r'[ōŏô]', 'o', id_text)
    id_text = re.sub(r'[ūŭû]', 'u', id_text)
    
    # Replace spaces and special chars with underscores
    id_text = re.sub(r'[^a-z0-9]', '_', id_text)
    id_text = re.sub(r'_+', '_', id_text)
    id_text = id_text.strip('_')
    
    return id_text

def process_json_file(file_path):
    """Process a single JSON file and return migration data"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract YouTube URLs from verses
    youtube_urls = []
    verses = data.get('content', {}).get('verses', [])
    for verse in verses:
        hawaiian_text = verse.get('hawaiian_text', '')
        english_text = verse.get('english_text', '')
        
        # Extract URLs
        urls_h = extract_youtube_urls(hawaiian_text)
        urls_e = extract_youtube_urls(english_text)
        youtube_urls.extend(urls_h + urls_e)
        
        # Clean the text content
        verse['hawaiian_text'] = clean_text_for_db(hawaiian_text)
        verse['english_text'] = clean_text_for_db(english_text)
    
    # Add existing media URLs
    existing_urls = data.get('media', {}).get('youtube_urls', [])
    youtube_urls.extend(existing_urls)
    youtube_urls = list(set(youtube_urls))  # Remove duplicates
    
    return {
        'source_data': data,
        'youtube_urls': youtube_urls,
        'canonical_id': None,  # To be set during canonical creation
        'needs_review': {
            'missing_composer': not data.get('attribution', {}).get('composer'),
            'multiple_translators': bool(data.get('attribution', {}).get('translator') and 
                                       data.get('attribution', {}).get('hawaiian_editor')),
            'title_needs_verification': len(data.get('title', {}).get('hawaiian', '')) < 3
        }
    }

def create_canonical_entries(processed_files, output_dir):
    """Create canonical mele entries and generate CSV for review"""
    canonical_entries = []
    review_data = []
    
    for file_data in processed_files:
        data = file_data['source_data']
        title_info = data.get('title', {})
        attribution = data.get('attribution', {})
        
        # Create canonical ID
        canonical_id = f"{normalize_id(title_info.get('hawaiian', ''))}_canonical"
        file_data['canonical_id'] = canonical_id
        
        # Create canonical entry
        canonical_entry = {
            'canonical_mele_id': canonical_id,
            'canonical_title_hawaiian': title_info.get('hawaiian', ''),
            'canonical_title_english': title_info.get('english', ''),
            'primary_composer': attribution.get('composer', ''),
            'primary_lyricist': attribution.get('lyricist', ''),
            'estimated_composition_date': '',  # Manual entry needed
            'cultural_significance_notes': '',  # Manual entry needed
            'created_by_editor': 'migration_script',
            'last_verified_date': datetime.now().date()
        }
        
        canonical_entries.append(canonical_entry)
        
        # Add to review data
        review_data.append({
            'canonical_id': canonical_id,
            'hawaiian_title': title_info.get('hawaiian', ''),
            'english_title': title_info.get('english', ''),
            'composer': attribution.get('composer', ''),
            'translator': attribution.get('translator', ''),
            'hawaiian_editor': attribution.get('hawaiian_editor', ''),
            'source_file': data.get('metadata', {}).get('source_file', ''),
            'needs_composer_research': not attribution.get('composer'),
            'has_multiple_editors': bool(attribution.get('translator') and attribution.get('hawaiian_editor')),
            'youtube_url_count': len(file_data['youtube_urls'])
        })
    
    # Write review CSV
    review_file = output_dir / 'canonical_review.csv'
    with open(review_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=review_data[0].keys())
        writer.writeheader()
        writer.writerows(review_data)
    
    print(f"Created review file: {review_file}")
    
    return canonical_entries

def insert_to_database(canonical_entries, processed_files, config):
    """Insert data into PostgreSQL database"""
    conn = psycopg2.connect(**config)
    cur = conn.cursor()
    
    try:
        # Insert canonical entries
        canonical_sql = """
        INSERT INTO canonical_mele (
            canonical_mele_id, canonical_title_hawaiian, canonical_title_english,
            primary_composer, primary_lyricist, estimated_composition_date,
            cultural_significance_notes, created_by_editor, last_verified_date
        ) VALUES %s ON CONFLICT (canonical_mele_id) DO NOTHING
        """
        
        canonical_values = [
            (
                entry['canonical_mele_id'], entry['canonical_title_hawaiian'],
                entry['canonical_title_english'], entry['primary_composer'],
                entry['primary_lyricist'], entry['estimated_composition_date'],
                entry['cultural_significance_notes'], entry['created_by_editor'],
                entry['last_verified_date']
            )
            for entry in canonical_entries
        ]
        
        execute_values(cur, canonical_sql, canonical_values)
        print(f"Inserted {len(canonical_entries)} canonical entries")
        
        # Insert source entries
        source_sql = """
        INSERT INTO mele_sources (
            id, canonical_mele_id, source_specific_title, composer, lyricist,
            translator, hawaiian_editor, source_editor, verses_json,
            structure_notes, source_file, source_publication, copyright_info,
            extraction_date, processing_status, raw_html_preserved,
            mele_type, themes, primary_location, island, cultural_elements
        ) VALUES %s ON CONFLICT (id) DO NOTHING
        """
        
        source_values = []
        for file_data in processed_files:
            data = file_data['source_data']
            title_info = data.get('title', {})
            attribution = data.get('attribution', {})
            content = data.get('content', {})
            metadata = data.get('metadata', {})
            classification = data.get('classification', {})
            
            source_values.append((
                data.get('id'),
                file_data['canonical_id'],
                title_info.get('hawaiian', ''),
                attribution.get('composer', ''),
                attribution.get('lyricist', ''),
                attribution.get('translator', ''),
                attribution.get('hawaiian_editor', ''),
                attribution.get('source_editor', ''),
                json.dumps(content.get('verses', [])),
                content.get('structure_notes', ''),
                metadata.get('source_file', ''),
                metadata.get('source_publication', ''),
                metadata.get('copyright', ''),
                metadata.get('extraction_date'),
                metadata.get('processing_status', ''),
                metadata.get('raw_html_preserved', False),
                json.dumps(classification.get('mele_type', [])),
                json.dumps(classification.get('themes', [])),
                classification.get('primary_location', ''),
                classification.get('island', ''),
                json.dumps(classification.get('cultural_elements', []))
            ))
        
        execute_values(cur, source_sql, source_values)
        print(f"Inserted {len(source_values)} source entries")
        
        # Insert media entries
        media_sql = """
        INSERT INTO mele_media (
            canonical_mele_id, media_type, url, title, description
        ) VALUES %s
        """
        
        media_values = []
        for file_data in processed_files:
            canonical_id = file_data['canonical_id']
            for url in file_data['youtube_urls']:
                media_values.append((
                    canonical_id,
                    'youtube',
                    url,
                    f"YouTube recording of {file_data['source_data'].get('title', {}).get('hawaiian', '')}",
                    'Extracted from source data'
                ))
        
        if media_values:
            execute_values(cur, media_sql, media_values)
            print(f"Inserted {len(media_values)} media entries")
        
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='Migrate JSON mele data to PostgreSQL')
    parser.add_argument('--input-dir', default='data/extracted_json', 
                       help='Directory containing JSON files')
    parser.add_argument('--output-dir', default='migration_reports',
                       help='Directory for migration reports')
    parser.add_argument('--dry-run', action='store_true',
                       help='Generate reports without inserting to database')
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Find JSON files
    json_files = list(input_dir.glob('*.json'))
    json_files = [f for f in json_files if 'summary' not in f.name.lower()]
    
    if not json_files:
        print(f"No JSON files found in {input_dir}")
        return
    
    print(f"Found {len(json_files)} JSON files to process")
    
    # Process files
    processed_files = []
    for json_file in json_files:
        print(f"Processing: {json_file.name}")
        file_data = process_json_file(json_file)
        processed_files.append(file_data)
    
    # Create canonical entries
    canonical_entries = create_canonical_entries(processed_files, output_dir)
    
    if args.dry_run:
        print("Dry run completed. Check migration_reports/ for review files.")
        return
    
    # Insert to database
    try:
        config = load_config()
        insert_to_database(canonical_entries, processed_files, config)
    except Exception as e:
        print(f"Database error: {e}")
        print("Please check your database configuration and connection.")
        return

if __name__ == '__main__':
    main()