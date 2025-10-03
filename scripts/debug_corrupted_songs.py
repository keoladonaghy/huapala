#!/usr/bin/env python3
"""
Debug script to examine corrupted verse structure
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

def examine_corrupted_songs():
    engine = create_engine(DB_URL)
    
    with engine.connect() as conn:
        # Get the corrupted songs
        corrupted_songs = ['mahina_o_hoku_canonical', 'iesu_me_ke_kanaka_waiwai_canonical']
        
        for song_id in corrupted_songs:
            query = text("""
            SELECT canonical_mele_id, verses_json 
            FROM mele_sources 
            WHERE canonical_mele_id = :song_id
            """)
            
            result = conn.execute(query, {"song_id": song_id})
            row = result.fetchone()
            
            if row:
                verses_json = row[1]
                
                print(f"\n{'='*60}")
                print(f"Song: {song_id}")
                print(f"Type: {type(verses_json)}")
                
                if isinstance(verses_json, str):
                    print(f"String content (first 500 chars): {repr(verses_json[:500])}")
                    
                    try:
                        parsed = json.loads(verses_json)
                        print(f"Successfully parsed JSON: {type(parsed)}")
                        if isinstance(parsed, list):
                            print(f"List with {len(parsed)} items")
                            for i, item in enumerate(parsed[:3]):
                                print(f"  Item {i}: {type(item)} - {repr(item)[:100]}")
                        elif isinstance(parsed, dict):
                            print(f"Dict with keys: {list(parsed.keys())}")
                    except json.JSONDecodeError as e:
                        print(f"JSON parsing failed: {e}")
                        # Try to see if it's a list of strings
                        try:
                            # Check if it looks like a Python list representation
                            if verses_json.startswith('[') and verses_json.endswith(']'):
                                print("Looks like a string representation of a list")
                                # Try to eval it (dangerous but for debugging)
                                evaluated = eval(verses_json)
                                print(f"Evaluated to: {type(evaluated)} with {len(evaluated)} items")
                                for i, item in enumerate(evaluated[:3]):
                                    print(f"  Item {i}: {type(item)} - {repr(item)[:100]}")
                        except Exception as eval_e:
                            print(f"Eval also failed: {eval_e}")

if __name__ == "__main__":
    examine_corrupted_songs()