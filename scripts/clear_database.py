#!/usr/bin/env python3
"""
Clear all song data from the database
"""
import os
import sys
import psycopg2

def get_database_url():
    """Get database URL from environment or construct from parts"""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url
    
    # Construct from Railway environment variables (like main.py does)
    host = os.getenv('PGHOST', 'localhost')
    port = os.getenv('PGPORT', '5432') 
    database = os.getenv('PGDATABASE', 'huapala')
    user = os.getenv('PGUSER', 'keola')
    password = os.getenv('PGPASSWORD', '')
    
    if password:
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    else:
        return f"postgresql://{user}@{host}:{port}/{database}"

def clear_song_data():
    """Clear all song-related data from database"""
    
    database_url = get_database_url()
    if not database_url:
        print("❌ No database connection available")
        return False
    
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        print("🗑️  Clearing song data from database...")
        
        # Get list of tables first
        cur.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename LIKE '%mele%' OR tablename LIKE '%song%'
            ORDER BY tablename
        """)
        tables = cur.fetchall()
        
        if tables:
            print(f"📋 Found {len(tables)} song-related tables:")
            for table in tables:
                print(f"   - {table[0]}")
        
        # Clear the main song tables (based on what we found)
        tables_to_clear = [
            'mele_sources',      # Clear first due to foreign key constraints
            'canonical_mele',    # Then clear the main table
            'mele_media',        # And media links
        ]
        
        for table in tables_to_clear:
            try:
                cur.execute(f"DELETE FROM {table}")
                deleted = cur.rowcount
                print(f"   ✅ Cleared {table}: {deleted} rows deleted")
            except psycopg2.Error as e:
                print(f"   ⚠️  Could not clear {table}: {e}")
        
        conn.commit()
        conn.close()
        
        print("✅ Database cleared successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        return False

if __name__ == "__main__":
    if "--confirm" not in sys.argv:
        print("⚠️  This will DELETE ALL song data from the database!")
        print("Add --confirm flag to proceed")
        sys.exit(1)
    
    clear_song_data()