"""
Populate normalized text columns for existing data
This script fills the normalized columns we created in setup_database.py
"""

import os
import psycopg2
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


def populate_canonical_mele_normalized(cursor):
    """Populate normalized columns for canonical_mele table"""
    print("Populating canonical_mele normalized columns...")
    
    # Get all canonical songs
    cursor.execute("""
        SELECT canonical_mele_id, canonical_title_hawaiian, canonical_title_english, primary_composer
        FROM canonical_mele
    """)
    
    songs = cursor.fetchall()
    updated_count = 0
    
    for song_id, title_hawaiian, title_english, composer in songs:
        # Normalize the titles and composer
        norm_hawaiian = normalize_title(title_hawaiian) if title_hawaiian else ""
        norm_english = normalize_title(title_english) if title_english else ""
        norm_composer = normalize_composer(composer) if composer else ""
        
        # Update the normalized columns
        cursor.execute("""
            UPDATE canonical_mele 
            SET normalized_title_hawaiian = %s,
                normalized_title_english = %s,
                normalized_composer = %s
            WHERE canonical_mele_id = %s
        """, (norm_hawaiian, norm_english, norm_composer, song_id))
        
        updated_count += 1
        
        print(f"✓ {song_id}: '{title_hawaiian}' → '{norm_hawaiian}'")
    
    print(f"Updated {updated_count} canonical songs")
    return updated_count


def populate_songbook_entries_normalized(cursor):
    """Populate normalized columns for songbook_entries table"""
    print("\nPopulating songbook_entries normalized columns...")
    
    # Process in batches to handle large dataset
    batch_size = 500
    offset = 0
    total_updated = 0
    
    while True:
        # Get batch of songbook entries
        cursor.execute("""
            SELECT id, printed_song_title, composer
            FROM songbook_entries
            ORDER BY id
            LIMIT %s OFFSET %s
        """, (batch_size, offset))
        
        entries = cursor.fetchall()
        
        if not entries:
            break  # No more entries
        
        batch_updates = []
        
        for entry_id, printed_title, composer in entries:
            # Normalize the title and composer
            norm_title = normalize_title(printed_title) if printed_title else ""
            norm_composer = normalize_composer(composer) if composer else ""
            
            batch_updates.append((norm_title, norm_composer, entry_id))
        
        # Batch update
        cursor.executemany("""
            UPDATE songbook_entries 
            SET normalized_printed_title = %s,
                normalized_composer = %s
            WHERE id = %s
        """, batch_updates)
        
        total_updated += len(batch_updates)
        offset += batch_size
        
        print(f"  Processed batch: {total_updated} entries updated...")
    
    print(f"Updated {total_updated} songbook entries")
    return total_updated


def show_normalization_examples(cursor):
    """Show some examples of the normalization results"""
    print("\n📋 Normalization Examples:")
    print("=" * 60)
    
    # Show canonical songs
    cursor.execute("""
        SELECT canonical_title_hawaiian, normalized_title_hawaiian, primary_composer, normalized_composer
        FROM canonical_mele 
        WHERE canonical_title_hawaiian IS NOT NULL
        LIMIT 5
    """)
    
    print("CANONICAL SONGS:")
    for orig_title, norm_title, orig_composer, norm_composer in cursor.fetchall():
        print(f"  Title: '{orig_title}' → '{norm_title}'")
        print(f"  Composer: '{orig_composer}' → '{norm_composer}'")
        print("-" * 40)
    
    # Show songbook entries
    cursor.execute("""
        SELECT printed_song_title, normalized_printed_title, composer, normalized_composer
        FROM songbook_entries 
        WHERE printed_song_title IS NOT NULL
        AND normalized_printed_title != ''
        LIMIT 5
    """)
    
    print("\nSONGBOOK ENTRIES:")
    for orig_title, norm_title, orig_composer, norm_composer in cursor.fetchall():
        print(f"  Title: '{orig_title}' → '{norm_title}'")
        print(f"  Composer: '{orig_composer}' → '{norm_composer}'")
        print("-" * 40)


def main():
    """Main function to populate all normalized data"""
    print("Populating normalized text columns...")
    
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Populate normalized data
        canonical_count = populate_canonical_mele_normalized(cursor)
        songbook_count = populate_songbook_entries_normalized(cursor)
        
        # Commit the changes
        conn.commit()
        
        # Show examples
        show_normalization_examples(cursor)
        
        print(f"\n✅ Successfully populated normalized data!")
        print(f"   - {canonical_count} canonical songs updated")
        print(f"   - {songbook_count} songbook entries updated")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error populating normalized data: {e}")
        raise


if __name__ == "__main__":
    # Set password if not in environment
    if not os.getenv('PGPASSWORD'):
        raise ValueError("PGPASSWORD environment variable is required")
    main()