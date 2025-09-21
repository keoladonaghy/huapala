#!/usr/bin/env python3
"""
Update database source_file references to use normalized filenames
"""

import psycopg2
import os
import unicodedata

def normalize_filename(filename):
    """Normalize a filename according to the specified rules"""
    
    # Remove .txt extension first to work with base name
    if filename.endswith('.txt'):
        base_name = filename[:-4]
    else:
        base_name = filename
    
    # Convert to lowercase
    normalized = base_name.lower()
    
    # Remove ʻokina (U+02BB and other variants)
    okina_chars = ['\u02bb', '\u2018', '\u2019', '`', "'"]
    for okina in okina_chars:
        normalized = normalized.replace(okina, '')
    
    # Replace vowel macrons with plain vowels
    macron_map = {
        'ā': 'a', 'ē': 'e', 'ī': 'i', 'ō': 'o', 'ū': 'u',
        'Ā': 'a', 'Ē': 'e', 'Ī': 'i', 'Ō': 'o', 'Ū': 'u'
    }
    
    for macron, plain in macron_map.items():
        normalized = normalized.replace(macron, plain)
    
    # Also handle decomposed Unicode (macron as combining character)
    normalized = unicodedata.normalize('NFD', normalized)
    normalized = ''.join(c for c in normalized if ord(c) != 0x0304)
    normalized = unicodedata.normalize('NFC', normalized)
    
    # Replace spaces with underscores
    normalized = normalized.replace(' ', '_')
    
    # Add .html extension
    normalized += '.html'
    
    return normalized

def update_source_file_paths(database_url):
    """Update source_file paths in the database to use normalized filenames"""
    
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    
    # Get all current source_file entries
    cur.execute("SELECT canonical_mele_id, source_file FROM mele_sources WHERE source_file IS NOT NULL")
    rows = cur.fetchall()
    
    print(f"Found {len(rows)} source_file entries to update:")
    print()
    
    updates = []
    
    for canonical_id, source_file in rows:
        if source_file.startswith('data/source_html/') and source_file.endswith('.txt'):
            # Extract just the filename
            old_filename = source_file.replace('data/source_html/', '')
            new_filename = normalize_filename(old_filename)
            new_source_file = f'data/source_html/{new_filename}'
            
            updates.append((canonical_id, source_file, new_source_file))
            print(f"{canonical_id}: '{source_file}' → '{new_source_file}'")
    
    if updates:
        print()
        print(f"Updating {len(updates)} database entries...")
        
        for canonical_id, old_path, new_path in updates:
            cur.execute("""
                UPDATE mele_sources 
                SET source_file = %s 
                WHERE canonical_mele_id = %s AND source_file = %s
            """, (new_path, canonical_id, old_path))
            print(f"✅ Updated {canonical_id}")
        
        conn.commit()
        print()
        print("Database updates complete!")
        
        # Verify the updates
        print()
        print("Current source_file paths:")
        cur.execute("SELECT canonical_mele_id, source_file FROM mele_sources WHERE source_file LIKE '%source_html%' ORDER BY canonical_mele_id")
        for canonical_id, source_file in cur.fetchall():
            print(f"  {canonical_id}: {source_file}")
    else:
        print("No updates needed.")
    
    cur.close()
    conn.close()

def main():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        return
    
    update_source_file_paths(database_url)

if __name__ == "__main__":
    main()