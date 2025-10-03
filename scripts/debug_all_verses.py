#!/usr/bin/env python3

import json
from database import SessionLocal, MeleSources

def debug_all_verses(song_id="bye_and_bye_hoi_mai_canonical"):
    """Debug all verses in the song"""
    db = SessionLocal()
    try:
        source = db.query(MeleSources).filter(MeleSources.canonical_mele_id == song_id).first()
        if source and source.verses_json:
            verses_data = json.loads(source.verses_json)
            print(f"Total verses: {len(verses_data)}")
            
            for i, verse in enumerate(verses_data):
                print(f"\n=== VERSE {i+1} ===")
                print(f"ID: {verse.get('id')}")
                print(f"Type: {verse.get('type')}")
                print(f"Number: {verse.get('number')}")
                print(f"Label: {verse.get('label')}")
                print(f"Lines: {len(verse.get('lines', []))}")
                
                for j, line in enumerate(verse.get('lines', [])):
                    print(f"  {j+1}: '{line.get('hawaiian_text', 'NO_HAW')}' | '{line.get('english_text', 'NO_ENG')}'")
        else:
            print("No verses found!")
    finally:
        db.close()

if __name__ == "__main__":
    debug_all_verses()