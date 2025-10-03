#!/usr/bin/env python3
"""
Debug MeleSources table structure to understand URL routing issue
"""
import os
import psycopg2

def get_database_url():
    """Get database URL from environment or construct from parts"""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url
    
    # Construct from Railway environment variables
    host = os.getenv('PGHOST', 'ep-young-silence-ad9wue88-pooler.c-2.us-east-1.aws.neon.tech')
    port = os.getenv('PGPORT', '5432') 
    database = os.getenv('PGDATABASE', 'neondb')
    user = os.getenv('PGUSER', 'neondb_owner')
    password = os.getenv('PGPASSWORD', '')
    
    return f"postgresql://{user}:{password}@{host}:{port}/{database}?sslmode=require"

def debug_mele_sources():
    """Check MeleSources table structure and data"""
    
    database_url = get_database_url()
    if not database_url:
        print("❌ No database connection available")
        return
    
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        print("🔍 Analyzing mele_sources table...")
        
        # Get table schema
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'mele_sources'
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        
        columns = cur.fetchall()
        print("\n📋 Table Schema:")
        for col in columns:
            print(f"   - {col[0]}: {col[1]} {'NULL' if col[2] == 'YES' else 'NOT NULL'} {f'DEFAULT {col[3]}' if col[3] else ''}")
        
        # Get primary key info
        cur.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_catalog = kcu.constraint_catalog
                AND tc.constraint_schema = kcu.constraint_schema
                AND tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_name = 'mele_sources'
                AND tc.table_schema = 'public'
        """)
        pk_columns = cur.fetchall()
        print(f"\n🔑 Primary Key: {[col[0] for col in pk_columns]}")
        
        # Sample some data to understand the issue
        cur.execute("SELECT id, canonical_mele_id FROM mele_sources LIMIT 5")
        rows = cur.fetchall()
        print(f"\n📊 Sample Data:")
        for row in rows:
            print(f"   ID: {row[0]} ({type(row[0]).__name__}), canonical_mele_id: {row[1]} ({type(row[1]).__name__})")
        
        # Check if there are any records with the specific ID mentioned in the error
        cur.execute("SELECT * FROM mele_sources WHERE canonical_mele_id = 'adios_ke_aloha_canonical_source'")
        problem_row = cur.fetchone()
        if problem_row:
            print(f"\n⚠️  Found problem record: {problem_row}")
        else:
            print(f"\n✅ No record found with canonical_mele_id = 'adios_ke_aloha_canonical_source'")
            
        # Check if there are any records with this pattern (ending in _source)
        cur.execute("SELECT canonical_mele_id FROM mele_sources WHERE canonical_mele_id LIKE '%_source' LIMIT 5")
        source_records = cur.fetchall()
        if source_records:
            print(f"\n🔍 Found records ending in '_source': {[r[0] for r in source_records]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    debug_mele_sources()