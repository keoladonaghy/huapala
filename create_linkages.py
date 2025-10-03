#!/usr/bin/env python3
"""
Songbook Linkage Matching Engine
Creates suggested matches between songs in the archive and songbook entries
"""

import json
import pandas as pd
from difflib import SequenceMatcher
import re
from typing import List, Dict, Tuple
import unicodedata

def normalize_title(title: str) -> str:
    """Normalize title for comparison"""
    if not title or pd.isna(title):
        return ""
    
    # Convert to lowercase
    title = str(title).lower()
    
    # Remove diacritics
    title = unicodedata.normalize('NFD', title)
    title = ''.join(c for c in title if unicodedata.category(c) != 'Mn')
    
    # Remove common prefixes/suffixes
    title = re.sub(r'^(na|ka|ke|o)\s+', '', title)
    title = re.sub(r'\s+(hula|song|waltz|march|polka)$', '', title)
    
    # Remove punctuation and extra spaces
    title = re.sub(r'[^\w\s]', ' ', title)
    title = re.sub(r'\s+', ' ', title).strip()
    
    return title

def calculate_similarity(title1: str, title2: str) -> float:
    """Calculate similarity between two titles"""
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    
    if not norm1 or not norm2:
        return 0.0
    
    # Exact match gets highest score
    if norm1 == norm2:
        return 1.0
    
    # Use sequence matcher for fuzzy matching
    return SequenceMatcher(None, norm1, norm2).ratio()

def find_matches(songs_data: List[Dict], songbook_entries: List[Dict], min_similarity: float = 0.75) -> List[Dict]:
    """Find potential matches between songs and songbook entries"""
    matches = []
    
    print(f"Processing {len(songs_data)} songs against {len(songbook_entries)} songbook entries...")
    
    for song in songs_data:
        song_titles = []
        
        # Collect all possible titles for the song
        if song.get('canonical_title_hawaiian'):
            song_titles.append(song['canonical_title_hawaiian'])
        if song.get('canonical_title_english'):
            song_titles.append(song['canonical_title_english'])
        
        # Get alternate titles from verses
        for verse in song.get('verses', []):
            if verse.get('verse_title_hawaiian'):
                song_titles.append(verse['verse_title_hawaiian'])
            if verse.get('verse_title_english'):
                song_titles.append(verse['verse_title_english'])
        
        # Remove duplicates
        song_titles = list(set([t for t in song_titles if t]))
        
        if not song_titles:
            continue
        
        # Check against each songbook entry
        for entry in songbook_entries:
            entry_titles = []
            
            # Collect all title variations from songbook entry
            for title_field in ['printed_song_title', 'eng_title_transl', 'modern_song_title', 'scripped_song_title', 'Song Title']:
                if entry.get(title_field) and not pd.isna(entry[title_field]):
                    entry_titles.append(entry[title_field])
            
            if not entry_titles:
                continue
            
            # Find best match between any song title and any entry title
            best_similarity = 0.0
            best_song_title = ""
            best_entry_title = ""
            
            for song_title in song_titles:
                for entry_title in entry_titles:
                    similarity = calculate_similarity(song_title, entry_title)
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_song_title = song_title
                        best_entry_title = entry_title
            
            # If similarity is above threshold, record the match
            if best_similarity >= min_similarity:
                match = {
                    'canonical_mele_id': song['canonical_mele_id'],
                    'song_title_matched': best_song_title,
                    'songbook_entry_title': best_entry_title,
                    'songbook_name': entry.get('songbook_name'),
                    'page': entry.get('page'),
                    'pub_year': entry.get('pub_year'),
                    'composer': entry.get('Composer'),
                    'similarity_score': round(best_similarity, 3),
                    'match_status': 'suggested',  # pending, approved, rejected
                    'timestamp': entry.get('timestamp'),
                    'songbook_entry_id': songbook_entries.index(entry)  # Simple ID for now
                }
                matches.append(match)
    
    # Sort by similarity score (highest first)
    matches.sort(key=lambda x: x['similarity_score'], reverse=True)
    
    return matches

def main():
    """Main execution function"""
    try:
        # Load song data
        print("Loading song data...")
        with open('docs/songs-data.json', 'r', encoding='utf-8') as f:
            songs_data = json.load(f)
        print(f"Loaded {len(songs_data)} songs")
        
        # Load songbook entries
        print("Loading songbook entries...")
        with open('data/songbooks/songbook_entries.json', 'r', encoding='utf-8') as f:
            songbook_entries = json.load(f)
        print(f"Loaded {len(songbook_entries)} songbook entries")
        
        # Find matches
        print("Finding matches...")
        matches = find_matches(songs_data, songbook_entries)
        
        print(f"Found {len(matches)} potential matches")
        
        # Save matches for the admin interface
        with open('data/songbooks/suggested_linkages.json', 'w', encoding='utf-8') as f:
            json.dump(matches, f, indent=2, ensure_ascii=False)
        
        # Show summary
        print("\nTop 10 matches:")
        for i, match in enumerate(matches[:10]):
            print(f"{i+1}. {match['song_title_matched']} -> {match['songbook_entry_title']}")
            print(f"   Songbook: {match['songbook_name']} (p. {match['page']}) - Score: {match['similarity_score']}")
            print()
        
        # Statistics
        high_confidence = [m for m in matches if m['similarity_score'] >= 0.9]
        medium_confidence = [m for m in matches if 0.8 <= m['similarity_score'] < 0.9]
        low_confidence = [m for m in matches if 0.75 <= m['similarity_score'] < 0.8]
        
        print(f"Match confidence breakdown:")
        print(f"  High (≥0.9): {len(high_confidence)} matches")
        print(f"  Medium (0.8-0.89): {len(medium_confidence)} matches")
        print(f"  Low (0.75-0.79): {len(low_confidence)} matches")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()