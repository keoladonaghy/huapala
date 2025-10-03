"""
Songbook Linkage System - Core Matching Engine
Implements three-tier confidence matching for Hawaiian songs
"""

import os
import sys
import psycopg2
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from difflib import SequenceMatcher

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from text_normalization import normalize_title, normalize_composer


class MatchingEngine:
    """Core engine for finding and scoring song matches between canonical and songbook entries"""
    
    def __init__(self, algorithm_version="v1.0"):
        self.algorithm_version = algorithm_version
        self.confidence_thresholds = {
            'high': 95,      # Auto-link without review
            'medium': 70,    # Queue for human review  
            'low': 0         # Manual review required
        }
    
    def get_database_connection(self):
        """Get database connection using existing credentials"""
        return psycopg2.connect(
            host='ep-young-silence-ad9wue88-pooler.c-2.us-east-1.aws.neon.tech',
            port=5432,
            database='neondb',
            user='neondb_owner',
            password=os.getenv('PGPASSWORD', '')
        )
    
    def calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two normalized titles using sequence matching"""
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
    
    def calculate_composer_similarity(self, composer1: str, composer2: str) -> float:
        """Calculate similarity between composer names"""
        if not composer1 or not composer2:
            return 0.0
        
        # Normalize both composers
        norm1 = normalize_composer(composer1)
        norm2 = normalize_composer(composer2)
        
        if norm1 == norm2:
            return 100.0  # Exact match
        
        # Use sequence matcher for fuzzy matching
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        return similarity * 100
    
    def calculate_confidence_score(self, canonical_song: Dict, songbook_entry: Dict) -> Tuple[float, str, Dict]:
        """
        Calculate confidence score for a potential match
        Returns: (confidence_score, match_method, scoring_details)
        """
        scoring_details = {}
        total_score = 0.0
        match_method = "fuzzy"
        
        # Title matching (50 points max)
        title_hawaiian = canonical_song.get('canonical_title_hawaiian', '')
        title_english = canonical_song.get('canonical_title_english', '')
        songbook_title = songbook_entry.get('printed_song_title', '')
        
        # Try both Hawaiian and English titles
        hawaiian_similarity = self.calculate_title_similarity(title_hawaiian, songbook_title)
        english_similarity = self.calculate_title_similarity(title_english, songbook_title)
        
        # Use the better title match
        title_score = max(hawaiian_similarity, english_similarity) * 0.5  # Scale to 50 points
        total_score += title_score
        
        scoring_details['title_hawaiian_similarity'] = hawaiian_similarity
        scoring_details['title_english_similarity'] = english_similarity
        scoring_details['title_score'] = title_score
        
        # Exact title match gets special treatment
        if hawaiian_similarity >= 95 or english_similarity >= 95:
            match_method = "exact"
        
        # Composer matching (30 points max)
        canonical_composer = canonical_song.get('primary_composer', '')
        songbook_composer = songbook_entry.get('composer', '')
        
        composer_similarity = self.calculate_composer_similarity(canonical_composer, songbook_composer)
        composer_score = composer_similarity * 0.3  # Scale to 30 points
        total_score += composer_score
        
        scoring_details['composer_similarity'] = composer_similarity
        scoring_details['composer_score'] = composer_score
        
        # Composer confirmation boosts confidence
        if composer_similarity >= 80:
            match_method = "composer_confirmed"
        
        # Publication date relevance (10 points max)
        # For now, give modest boost if publication year exists
        pub_year = songbook_entry.get('pub_year')
        if pub_year and str(pub_year).isdigit():
            date_score = 5.0  # Modest boost for having publication data
            total_score += date_score
            scoring_details['date_score'] = date_score
        
        # Multiple songbook appearances (5 points each - future enhancement)
        # This would require checking for other entries with same canonical_mele_id
        
        scoring_details['total_score'] = total_score
        scoring_details['match_method'] = match_method
        
        return total_score, match_method, scoring_details
    
    def find_matches_for_song(self, canonical_mele_id: str) -> List[Dict]:
        """Find all potential matches for a specific canonical song"""
        conn = self.get_database_connection()
        cursor = conn.cursor()
        
        try:
            # Get canonical song data
            cursor.execute("""
                SELECT canonical_mele_id, canonical_title_hawaiian, canonical_title_english, primary_composer
                FROM canonical_mele 
                WHERE canonical_mele_id = %s
            """, (canonical_mele_id,))
            
            canonical_data = cursor.fetchone()
            if not canonical_data:
                return []
            
            canonical_song = {
                'canonical_mele_id': canonical_data[0],
                'canonical_title_hawaiian': canonical_data[1],
                'canonical_title_english': canonical_data[2],
                'primary_composer': canonical_data[3]
            }
            
            # Get all songbook entries that don't already have a canonical link
            cursor.execute("""
                SELECT id, printed_song_title, composer, pub_year, songbook_name
                FROM songbook_entries 
                WHERE canonical_mele_id IS NULL
                ORDER BY id
            """)
            
            songbook_entries = cursor.fetchall()
            matches = []
            
            for entry_data in songbook_entries:
                songbook_entry = {
                    'id': entry_data[0],
                    'printed_song_title': entry_data[1],
                    'composer': entry_data[2],
                    'pub_year': entry_data[3],
                    'songbook_name': entry_data[4]
                }
                
                # Calculate confidence score
                confidence, method, details = self.calculate_confidence_score(canonical_song, songbook_entry)
                
                # Only include matches above minimum threshold (20% similarity)
                if confidence >= 20:
                    match_record = {
                        'canonical_mele_id': canonical_mele_id,
                        'songbook_entry_id': songbook_entry['id'],
                        'songbook_entry': songbook_entry,
                        'confidence': confidence,
                        'match_method': method,
                        'scoring_details': details,
                        'tier': self.get_confidence_tier(confidence)
                    }
                    matches.append(match_record)
            
            # Sort by confidence (highest first)
            matches.sort(key=lambda x: x['confidence'], reverse=True)
            
            return matches
            
        finally:
            cursor.close()
            conn.close()
    
    def get_confidence_tier(self, confidence: float) -> str:
        """Determine confidence tier based on score"""
        if confidence >= self.confidence_thresholds['high']:
            return 'high'
        elif confidence >= self.confidence_thresholds['medium']:
            return 'medium'
        else:
            return 'low'
    
    def save_match(self, match_record: Dict, status: str = None) -> bool:
        """Save a match to the matching_status table"""
        conn = self.get_database_connection()
        cursor = conn.cursor()
        
        try:
            # Determine status based on confidence tier if not provided
            if status is None:
                tier = match_record['tier']
                if tier == 'high':
                    status = 'auto_linked'
                elif tier == 'medium':
                    status = 'needs_review'
                else:
                    status = 'needs_review'  # Low confidence also needs review
            
            # Insert match record
            cursor.execute("""
                INSERT INTO matching_status (
                    canonical_mele_id, songbook_entry_id, match_confidence, 
                    match_method, match_status, algorithm_version, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (canonical_mele_id, songbook_entry_id) 
                DO UPDATE SET 
                    match_confidence = EXCLUDED.match_confidence,
                    match_method = EXCLUDED.match_method,
                    match_status = EXCLUDED.match_status,
                    algorithm_version = EXCLUDED.algorithm_version,
                    notes = EXCLUDED.notes,
                    matched_at = NOW()
            """, (
                match_record['canonical_mele_id'],
                match_record['songbook_entry_id'],
                match_record['confidence'],
                match_record['match_method'],
                status,
                self.algorithm_version,
                f"Scoring details: {match_record['scoring_details']}"
            ))
            
            # For high-confidence matches, also update the songbook_entries table
            if status == 'auto_linked':
                cursor.execute("""
                    UPDATE songbook_entries 
                    SET canonical_mele_id = %s 
                    WHERE id = %s
                """, (match_record['canonical_mele_id'], match_record['songbook_entry_id']))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"Error saving match: {e}")
            return False
            
        finally:
            cursor.close()
            conn.close()
    
    def process_song_matches(self, canonical_mele_id: str, auto_link_high_confidence: bool = True) -> Dict:
        """Process all matches for a single song"""
        matches = self.find_matches_for_song(canonical_mele_id)
        
        results = {
            'canonical_mele_id': canonical_mele_id,
            'total_matches': len(matches),
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'auto_linked': 0,
            'queued_for_review': 0,
            'matches': matches
        }
        
        for match in matches:
            tier = match['tier']
            
            if tier == 'high':
                results['high_confidence'] += 1
                if auto_link_high_confidence:
                    if self.save_match(match, 'auto_linked'):
                        results['auto_linked'] += 1
                else:
                    if self.save_match(match, 'needs_review'):
                        results['queued_for_review'] += 1
                        
            elif tier == 'medium':
                results['medium_confidence'] += 1
                if self.save_match(match, 'needs_review'):
                    results['queued_for_review'] += 1
                    
            else:  # low confidence
                results['low_confidence'] += 1
                if self.save_match(match, 'needs_review'):
                    results['queued_for_review'] += 1
        
        return results


def main():
    """Main function for testing the matching engine"""
    print("🎵 Songbook Linkage System - Matching Engine Test")
    print("=" * 60)
    
    # Set password if not in environment
    if not os.getenv('PGPASSWORD'):
        raise ValueError("PGPASSWORD environment variable is required")
    
    engine = MatchingEngine()
    
    # Get list of canonical songs to test
    conn = engine.get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT canonical_mele_id, canonical_title_hawaiian, canonical_title_english 
            FROM canonical_mele 
            ORDER BY canonical_mele_id
            LIMIT 5
        """)
        
        test_songs = cursor.fetchall()
        
        print(f"Testing matching engine with {len(test_songs)} songs...\n")
        
        for song_data in test_songs:
            canonical_id = song_data[0]
            title_hawaiian = song_data[1] or ""
            title_english = song_data[2] or ""
            
            print(f"🔍 Processing: {canonical_id}")
            print(f"   Hawaiian: {title_hawaiian}")
            print(f"   English: {title_english}")
            
            results = engine.process_song_matches(canonical_id, auto_link_high_confidence=False)
            
            print(f"   📊 Results: {results['total_matches']} potential matches")
            print(f"      High confidence: {results['high_confidence']}")
            print(f"      Medium confidence: {results['medium_confidence']}")
            print(f"      Low confidence: {results['low_confidence']}")
            
            # Show top matches
            if results['matches']:
                print(f"   🏆 Top matches:")
                for i, match in enumerate(results['matches'][:3]):
                    entry = match['songbook_entry']
                    print(f"      {i+1}. {match['confidence']:.1f}% - '{entry['printed_song_title']}' by {entry['composer']} ({match['tier']} confidence)")
            
            print("-" * 50)
        
        print("\n✅ Matching engine test completed!")
        
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()