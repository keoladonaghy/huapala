"""
Simple test script to validate the songbook linkage matching approach
"""

import os
import sys
import psycopg2
from difflib import SequenceMatcher

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from text_normalization import normalize_title, normalize_composer


def get_database_connection():
    """Get database connection using existing credentials"""
    return psycopg2.connect(
        host='ep-young-silence-ad9wue88-pooler.c-2.us-east-1.aws.neon.tech',
        port=5432,
        database='neondb',
        user='neondb_owner',
        password=os.getenv('PGPASSWORD', '')
    )


def calculate_title_similarity(title1: str, title2: str) -> float:
    """Calculate similarity between two normalized titles"""
    if not title1 or not title2:
        return 0.0
    
    # Normalize both titles
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    
    if norm1 == norm2:
        return 100.0  # Exact match
    
    # Use sequence matcher for fuzzy matching
    similarity = SequenceMatcher(None, norm1, norm2).ratio()
    return similarity * 100


def test_matching():
    """Test the matching approach with actual data"""
    print("🎵 Songbook Linkage System - Matching Test")
    print("=" * 60)
    
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Get a few canonical songs to test
        cursor.execute("""
            SELECT canonical_mele_id, canonical_title_hawaiian, canonical_title_english, primary_composer
            FROM canonical_mele 
            ORDER BY canonical_mele_id
            LIMIT 5
        """)
        
        canonical_songs = cursor.fetchall()
        
        # Get some songbook entries to test against
        cursor.execute("""
            SELECT id, printed_song_title, composer, songbook_name
            FROM songbook_entries 
            WHERE printed_song_title IS NOT NULL
            ORDER BY id
            LIMIT 20
        """)
        
        songbook_entries = cursor.fetchall()
        
        print(f"Testing {len(canonical_songs)} canonical songs against {len(songbook_entries)} songbook entries...\n")
        
        high_confidence_matches = 0
        medium_confidence_matches = 0
        
        for canonical in canonical_songs:
            canonical_id, title_hawaiian, title_english, composer = canonical
            
            print(f"🔍 Testing: {canonical_id}")
            print(f"   Hawaiian: '{title_hawaiian or 'N/A'}'")
            print(f"   English: '{title_english or 'N/A'}'")
            print(f"   Composer: '{composer or 'N/A'}'")
            
            best_matches = []
            
            for entry in songbook_entries:
                entry_id, printed_title, entry_composer, songbook = entry
                
                # Calculate title similarities
                hawaiian_sim = calculate_title_similarity(title_hawaiian or "", printed_title)
                english_sim = calculate_title_similarity(title_english or "", printed_title)
                
                # Use the better title match
                title_similarity = max(hawaiian_sim, english_sim)
                
                # Calculate composer similarity
                composer_similarity = 0.0
                if composer and entry_composer:
                    composer_similarity = SequenceMatcher(None, 
                        normalize_composer(composer), 
                        normalize_composer(entry_composer)
                    ).ratio() * 100
                
                # Simple confidence calculation (title 50 points + composer 30 points)
                confidence = (title_similarity * 0.5) + (composer_similarity * 0.3)
                
                if confidence >= 20:  # Only consider matches above 20% confidence
                    best_matches.append({
                        'entry_id': entry_id,
                        'printed_title': printed_title,
                        'composer': entry_composer or 'N/A',
                        'songbook': songbook,
                        'confidence': confidence,
                        'title_similarity': title_similarity,
                        'composer_similarity': composer_similarity
                    })
            
            # Sort by confidence
            best_matches.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Show top 3 matches
            if best_matches:
                print(f"   📊 Top matches found:")
                for i, match in enumerate(best_matches[:3]):
                    tier = "HIGH" if match['confidence'] >= 70 else "MEDIUM" if match['confidence'] >= 40 else "LOW"
                    print(f"      {i+1}. {match['confidence']:.1f}% ({tier}) - '{match['printed_title']}'")
                    print(f"         By: {match['composer']} | In: {match['songbook']}")
                    print(f"         Title similarity: {match['title_similarity']:.1f}%")
                    print(f"         Composer similarity: {match['composer_similarity']:.1f}%")
                
                # Count confidence tiers
                top_match = best_matches[0]
                if top_match['confidence'] >= 70:
                    high_confidence_matches += 1
                elif top_match['confidence'] >= 40:
                    medium_confidence_matches += 1
            else:
                print(f"   ❌ No potential matches found")
            
            print("-" * 50)
        
        print(f"\n📈 Overall Results:")
        print(f"   High confidence matches (≥70%): {high_confidence_matches}")
        print(f"   Medium confidence matches (40-69%): {medium_confidence_matches}")
        print(f"   Songs with no good matches: {len(canonical_songs) - high_confidence_matches - medium_confidence_matches}")
        
        print(f"\n✅ Matching test completed!")
        
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Set password if not in environment
    if not os.getenv('PGPASSWORD'):
        raise ValueError("PGPASSWORD environment variable is required")
    test_matching()