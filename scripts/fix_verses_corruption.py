#!/usr/bin/env python3
"""
Fix Verses JSON Corruption in Database

This script fixes verses_json records that have the wrong format:
- Corrupted format: [{"id": "v1", ...}]  (just the array)
- Correct format: {"verses": [{"id": "v1", ...}], "processing_metadata": {}}

The script will:
1. Find all records with corrupted verses_json format
2. Wrap them in the proper structure
3. Update the database
4. Generate a report of what was fixed
"""

import os
import json
import sys
from sqlalchemy import create_engine, text
from datetime import datetime
# Add parent directory to path to import auth
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import get_database_url

# Database connection
DB_URL = get_database_url()

def detect_corrupted_format(verses_json_data):
    """
    Detect if verses_json is in the corrupted format
    Returns: True if corrupted, False if correct
    """
    if isinstance(verses_json_data, str):
        try:
            parsed = json.loads(verses_json_data)
        except json.JSONDecodeError:
            return True  # Invalid JSON is considered corrupted
    elif isinstance(verses_json_data, (list, dict)):
        parsed = verses_json_data
    else:
        return True  # Unknown type is corrupted
    
    # Correct format should be a dict with 'verses' key
    if isinstance(parsed, dict) and 'verses' in parsed:
        return False  # This is the correct format
    
    # If it's a list or dict without 'verses', it's corrupted
    return True

def fix_verses_format(verses_json_data):
    """
    Convert corrupted format to correct format
    """
    if isinstance(verses_json_data, str):
        try:
            parsed = json.loads(verses_json_data)
        except json.JSONDecodeError:
            # If we can't parse it, return empty structure
            return {"verses": [], "processing_metadata": {}}
    else:
        parsed = verses_json_data
    
    # If it's already in correct format, return as-is
    if isinstance(parsed, dict) and 'verses' in parsed:
        return parsed
    
    # If it's a list (corrupted format), wrap it
    if isinstance(parsed, list):
        return {
            "verses": parsed,
            "processing_metadata": {}
        }
    
    # If it's a dict without 'verses' key, assume it's a single verse
    if isinstance(parsed, dict):
        return {
            "verses": [parsed],
            "processing_metadata": {}
        }
    
    # Fallback: empty structure
    return {"verses": [], "processing_metadata": {}}

def main():
    """Main migration function"""
    engine = create_engine(DB_URL)
    
    fixed_count = 0
    error_count = 0
    total_count = 0
    
    print("Starting verses_json corruption fix...")
    print(f"Timestamp: {datetime.now()}")
    print("-" * 60)
    
    with engine.connect() as conn:
        # Get all mele_sources records with verses_json
        query = text("""
        SELECT canonical_mele_id, verses_json 
        FROM mele_sources 
        WHERE verses_json IS NOT NULL
        ORDER BY canonical_mele_id
        """)
        
        results = conn.execute(query).fetchall()
        total_count = len(results)
        
        print(f"Found {total_count} records with verses_json data")
        print()
        
        for row in results:
            canonical_mele_id = row[0]
            verses_json_data = row[1]
            
            try:
                # Check if this record needs fixing
                if detect_corrupted_format(verses_json_data):
                    print(f"Fixing: {canonical_mele_id}")
                    
                    # Fix the format
                    fixed_data = fix_verses_format(verses_json_data)
                    
                    # Update the database
                    update_query = text("""
                    UPDATE mele_sources 
                    SET verses_json = :fixed_data,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE canonical_mele_id = :song_id
                    """)
                    
                    conn.execute(update_query, {
                        "fixed_data": json.dumps(fixed_data, ensure_ascii=False),
                        "song_id": canonical_mele_id
                    })
                    
                    fixed_count += 1
                else:
                    print(f"Already correct: {canonical_mele_id}")
                    
            except Exception as e:
                print(f"ERROR fixing {canonical_mele_id}: {e}")
                error_count += 1
        
        # Commit all changes
        conn.commit()
    
    print()
    print("-" * 60)
    print("Migration Summary:")
    print(f"Total records processed: {total_count}")
    print(f"Records fixed: {fixed_count}")
    print(f"Records already correct: {total_count - fixed_count - error_count}")
    print(f"Errors encountered: {error_count}")
    print(f"Timestamp: {datetime.now()}")
    
    if error_count > 0:
        print(f"\nWARNING: {error_count} errors occurred during migration!")
        sys.exit(1)
    else:
        print("\nMigration completed successfully!")

if __name__ == "__main__":
    main()