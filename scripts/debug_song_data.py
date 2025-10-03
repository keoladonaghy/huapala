#!/usr/bin/env python3

import json
from database import SessionLocal, CanonicalMele, MeleSources, MeleMedia

def debug_song_data(song_id="bye_and_bye_hoi_mai_canonical"):
    """Debug song data structure"""
    db = SessionLocal()
    try:
        # Get canonical song data
        canonical_song = db.query(CanonicalMele).filter(CanonicalMele.canonical_mele_id == song_id).first()
        print(f"Canonical song: {canonical_song}")
        if canonical_song:
            print(f"  Title Hawaiian: {canonical_song.canonical_title_hawaiian}")
            print(f"  Title English: {canonical_song.canonical_title_english}")
        
        # Get related source data
        source_data = db.query(MeleSources).filter(MeleSources.canonical_mele_id == song_id).first()
        print(f"\nSource data: {source_data}")
        if source_data:
            print(f"  Source ID: {source_data.id}")
            print(f"  Verses JSON exists: {source_data.verses_json is not None}")
            if source_data.verses_json:
                print(f"  Verses JSON type: {type(source_data.verses_json)}")
                # Parse the JSON string
                try:
                    verses_data = json.loads(source_data.verses_json)
                    print(f"  Parsed verses data type: {type(verses_data)}")
                    if isinstance(verses_data, dict):
                        print(f"  Parsed verses data keys: {verses_data.keys()}")
                        if 'verses' in verses_data:
                            verses = verses_data['verses']
                            print(f"  Number of verses: {len(verses) if isinstance(verses, list) else 'Not a list'}")
                            if isinstance(verses, list) and len(verses) > 0:
                                print(f"  First verse keys: {verses[0].keys()}")
                                print(f"  First verse: {verses[0]}")
                    elif isinstance(verses_data, list):
                        print(f"  Verses data is a list with {len(verses_data)} items")
                        if len(verses_data) > 0:
                            print(f"  First item type: {type(verses_data[0])}")
                            print(f"  First item keys: {verses_data[0].keys() if isinstance(verses_data[0], dict) else 'Not a dict'}")
                            print(f"  First item: {verses_data[0]}")
                except json.JSONDecodeError as e:
                    print(f"  JSON parse error: {e}")
                    print(f"  Raw data (first 200 chars): {source_data.verses_json[:200]}...")
        
        # Get related media data
        media_data = db.query(MeleMedia).filter(MeleMedia.canonical_mele_id == song_id).all()
        print(f"\nMedia data count: {len(media_data)}")
        
        return {
            "canonical_song": canonical_song,
            "source": source_data,
            "media": media_data
        }
    finally:
        db.close()

if __name__ == "__main__":
    debug_song_data()