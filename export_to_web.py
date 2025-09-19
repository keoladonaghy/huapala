#!/usr/bin/env python3
"""
Export Database to Web JSON

Exports the PostgreSQL database content to a JSON file for the web interface.
This creates a static data file that can be served by GitHub Pages.
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor

# Database configuration (same as migration script)
DB_CONFIG = {
    'host': 'ep-young-silence-ad9wue88-pooler.c-2.us-east-1.aws.neon.tech',
    'database': 'neondb',
    'user': 'neondb_owner',
    'password': 'npg_Ic2Qq1ErOykl',
    'port': 5432,
    'sslmode': 'require'
}

def export_songs_data():
    """Export all song data to JSON for web interface"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Query to get all song data with related information
        query = """
        SELECT 
            cm.canonical_mele_id,
            cm.canonical_title_hawaiian,
            cm.canonical_title_english,
            cm.primary_composer,
            cm.primary_lyricist,
            cm.estimated_composition_date,
            cm.cultural_significance_notes,
            ms.composer,
            ms.translator,
            ms.hawaiian_editor,
            ms.source_file,
            ms.source_publication,
            ms.copyright_info,
            ms.verses_json,
            ms.primary_location,
            ms.island,
            ms.themes,
            ms.mele_type,
            ms.cultural_elements,
            COUNT(mm.id) as youtube_count,
            ARRAY_AGG(mm.url) FILTER (WHERE mm.url IS NOT NULL) as youtube_urls
        FROM canonical_mele cm
        LEFT JOIN mele_sources ms ON cm.canonical_mele_id = ms.canonical_mele_id
        LEFT JOIN mele_media mm ON cm.canonical_mele_id = mm.canonical_mele_id
        GROUP BY 
            cm.canonical_mele_id, cm.canonical_title_hawaiian, cm.canonical_title_english,
            cm.primary_composer, cm.primary_lyricist, cm.estimated_composition_date,
            cm.cultural_significance_notes, ms.composer, ms.translator, ms.hawaiian_editor,
            ms.source_file, ms.source_publication, ms.copyright_info, ms.verses_json,
            ms.primary_location, ms.island, ms.themes, ms.mele_type, ms.cultural_elements
        ORDER BY cm.canonical_title_hawaiian
        """
        
        cur.execute(query)
        rows = cur.fetchall()
        
        # Convert to list of dictionaries and process
        songs_data = []
        for row in rows:
            song = dict(row)
            
            # Parse JSON fields
            if song['verses_json']:
                try:
                    song['verses'] = json.loads(song['verses_json'])
                except:
                    song['verses'] = []
            else:
                song['verses'] = []
            
            # Clean up None values and empty arrays
            if song['youtube_urls'] and song['youtube_urls'][0] is None:
                song['youtube_urls'] = []
            elif not song['youtube_urls']:
                song['youtube_urls'] = []
                
            if song['youtube_count'] == 0:
                song['youtube_count'] = None
                
            # Remove the raw JSON field
            del song['verses_json']
            
            songs_data.append(song)
        
        # Write to JSON file for web interface
        with open('docs/songs-data.json', 'w', encoding='utf-8') as f:
            json.dump(songs_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Exported {len(songs_data)} songs to docs/songs-data.json")
        print("Songs exported:")
        for song in songs_data:
            print(f"  - {song['canonical_title_hawaiian']}")
        
    except Exception as e:
        print(f"Error exporting data: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    export_songs_data()