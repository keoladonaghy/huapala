#!/usr/bin/env python3
"""
Debug script to examine verse structure in the database
"""
import os
import json
from sqlalchemy import create_engine, text
# Add parent directory to path to import auth
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import get_database_url

# Database connection
DB_URL = get_database_url()

def investigate_verse_structure():
    engine = create_engine(DB_URL)
    
    with engine.connect() as conn:
        # Get a few songs with verses_json data
        query = text("""
        SELECT canonical_mele_id, verses_json 
        FROM mele_sources 
        WHERE verses_json IS NOT NULL 
        LIMIT 3
        """)
        
        results = conn.execute(query)
        
        for row in results:
            song_id = row[0]
            verses_json = row[1]
            
            print(f"\n{'='*60}")
            print(f"Song: {song_id}")
            print(f"Type of verses_json: {type(verses_json)}")
            
            if isinstance(verses_json, str):
                print("Format: JSON String")
                try:
                    parsed = json.loads(verses_json)
                    print(f"Parsed structure keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'Not a dict'}")
                    
                    if isinstance(parsed, dict) and 'verses' in parsed:
                        verses = parsed['verses']
                        print(f"Number of verses: {len(verses)}")
                        
                        for i, verse in enumerate(verses[:2]):  # Show first 2 verses
                            print(f"\n--- Verse {i+1} ---")
                            print(f"Verse keys: {list(verse.keys()) if isinstance(verse, dict) else 'Not a dict'}")
                            
                            if isinstance(verse, dict) and 'lines' in verse:
                                lines = verse['lines']
                                print(f"Number of lines: {len(lines)}")
                                
                                for j, line in enumerate(lines[:2]):  # Show first 2 lines
                                    print(f"  Line {j+1}: {line}")
                    
                except json.JSONDecodeError as e:
                    print(f"JSON Parse Error: {e}")
                    print(f"Raw content (first 200 chars): {verses_json[:200]}")
                    
            elif isinstance(verses_json, dict):
                print("Format: Python Dictionary")
                print(f"Dict keys: {list(verses_json.keys())}")
                
                if 'verses' in verses_json:
                    verses = verses_json['verses']
                    print(f"Number of verses: {len(verses)}")
                    
                    for i, verse in enumerate(verses[:2]):  # Show first 2 verses
                        print(f"\n--- Verse {i+1} ---")
                        print(f"Verse keys: {list(verse.keys()) if isinstance(verse, dict) else 'Not a dict'}")
                        print(f"Verse type: {type(verse)}")
                        
                        if isinstance(verse, dict) and 'lines' in verse:
                            lines = verse['lines']
                            print(f"Number of lines: {len(lines)}")
                            
                            for j, line in enumerate(lines[:2]):  # Show first 2 lines
                                print(f"  Line {j+1}: {line}")
                                
            elif isinstance(verses_json, list):
                print("Format: Python List")
                print(f"Number of items: {len(verses_json)}")
                
                for i, item in enumerate(verses_json[:2]):  # Show first 2 items
                    print(f"\n--- Item {i+1} ---")
                    print(f"Item type: {type(item)}")
                    print(f"Item content: {item}")
            
            else:
                print(f"Unknown format: {type(verses_json)}")
                print(f"Content: {verses_json}")

if __name__ == "__main__":
    investigate_verse_structure()