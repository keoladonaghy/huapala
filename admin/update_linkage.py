#!/usr/bin/env python3
"""
Simple script to update songbook entry linkages
"""

import sys
import json
import psycopg2
import os

def update_songbook_linkage(songbook_entry_id, canonical_mele_id):
    """Update the songbook entry with the canonical mele ID"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host='localhost',
            user='keola',
            database='huapala',
            password=os.getenv('PGPASSWORD', '')
        )
        
        cur = conn.cursor()
        
        # Update the songbook entry with the canonical mele ID
        cur.execute("""
            UPDATE songbook_entries 
            SET canonical_mele_id = %s 
            WHERE id = %s
        """, (canonical_mele_id, songbook_entry_id))
        
        if cur.rowcount > 0:
            conn.commit()
            print(f"✅ Successfully linked songbook entry {songbook_entry_id} to song {canonical_mele_id}")
            return True
        else:
            print(f"❌ No songbook entry found with ID {songbook_entry_id}")
            return False
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def process_approved_linkages(linkages_file):
    """Process a JSON file of approved linkages"""
    try:
        with open(linkages_file, 'r') as f:
            linkages = json.load(f)
        
        approved_count = 0
        for linkage in linkages:
            if linkage.get('match_status') == 'approved':
                success = update_songbook_linkage(
                    linkage['songbook_entry_id'],
                    linkage['canonical_mele_id']
                )
                if success:
                    approved_count += 1
        
        print(f"\n📊 Processed {approved_count} approved linkages")
        
    except Exception as e:
        print(f"❌ Error processing linkages file: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage:")
        print("  python3 update_linkage.py <songbook_entry_id> <canonical_mele_id>")
        print("  python3 update_linkage.py --file <linkages.json>")
        sys.exit(1)
    
    if sys.argv[1] == "--file":
        process_approved_linkages(sys.argv[2])
    else:
        songbook_entry_id = int(sys.argv[1])
        canonical_mele_id = sys.argv[2]
        update_songbook_linkage(songbook_entry_id, canonical_mele_id)