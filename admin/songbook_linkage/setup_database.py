"""
Songbook Linkage System - Database Setup
Creates tables and columns needed for Phase 1 implementation
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def get_database_connection():
    """Get database connection using existing credentials"""
    return psycopg2.connect(
        host='ep-young-silence-ad9wue88-pooler.c-2.us-east-1.aws.neon.tech',
        port=5432,
        database='neondb',
        user='neondb_owner',
        password=os.getenv('PGPASSWORD', '')
    )


def create_matching_status_table(cursor):
    """Create the matching_status table to track all linkage operations"""
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS matching_status (
        id SERIAL PRIMARY KEY,
        canonical_mele_id VARCHAR REFERENCES canonical_mele(canonical_mele_id),
        songbook_entry_id INTEGER REFERENCES songbook_entries(id),
        match_confidence DECIMAL(5,2) CHECK (match_confidence >= 0 AND match_confidence <= 100),
        match_method VARCHAR CHECK (match_method IN ('exact', 'fuzzy', 'manual', 'composer_confirmed')),
        match_status VARCHAR CHECK (match_status IN ('auto_linked', 'needs_review', 'rejected', 'confirmed')),
        matched_at TIMESTAMP DEFAULT NOW(),
        reviewed_at TIMESTAMP,
        reviewed_by VARCHAR,
        algorithm_version VARCHAR DEFAULT 'v1.0',
        notes TEXT,
        created_at TIMESTAMP DEFAULT NOW(),
        
        -- Ensure unique combinations
        UNIQUE(canonical_mele_id, songbook_entry_id)
    );
    """
    
    cursor.execute(create_table_sql)
    print("✓ Created matching_status table")


def add_normalized_columns(cursor):
    """Add normalized text columns for fast searching"""
    
    # Add normalized columns if they don't exist
    normalized_columns = [
        ("canonical_mele", "normalized_title_hawaiian"),
        ("canonical_mele", "normalized_title_english"), 
        ("canonical_mele", "normalized_composer"),
        ("songbook_entries", "normalized_printed_title"),
        ("songbook_entries", "normalized_composer")
    ]
    
    for table, column in normalized_columns:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} VARCHAR;")
            print(f"✓ Added {table}.{column}")
        except psycopg2.errors.DuplicateColumn:
            print(f"- {table}.{column} already exists")
            

def add_dublin_core_columns(cursor):
    """Add Dublin Core metadata columns for future use"""
    
    dublin_core_columns = [
        ("songbook_entries", "dc_identifier", "VARCHAR"),      # ISBN, catalog number
        ("songbook_entries", "dc_date", "VARCHAR"),           # Publication date
        ("songbook_entries", "dc_publisher", "VARCHAR"),      # Publisher name  
        ("songbook_entries", "dc_subject", "VARCHAR"),        # Subject keywords
        ("songbook_entries", "dc_type", "VARCHAR"),           # Resource type
        ("songbook_entries", "dc_format", "VARCHAR"),         # Physical format
        ("songbook_entries", "dc_language", "VARCHAR")        # Language code
    ]
    
    for table, column, datatype in dublin_core_columns:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {datatype};")
            print(f"✓ Added {table}.{column} ({datatype})")
        except psycopg2.errors.DuplicateColumn:
            print(f"- {table}.{column} already exists")


def create_indexes(cursor):
    """Create indexes for performance"""
    
    indexes = [
        ("idx_matching_status_needs_review", "matching_status", "match_status", "WHERE match_status = 'needs_review'"),
        ("idx_matching_status_confidence", "matching_status", "match_confidence DESC", ""),
        ("idx_canonical_normalized_hawaiian", "canonical_mele", "normalized_title_hawaiian", ""),
        ("idx_canonical_normalized_english", "canonical_mele", "normalized_title_english", ""),
        ("idx_canonical_normalized_composer", "canonical_mele", "normalized_composer", ""),
        ("idx_songbook_normalized_title", "songbook_entries", "normalized_printed_title", ""),
        ("idx_songbook_normalized_composer", "songbook_entries", "normalized_composer", "")
    ]
    
    for index_name, table, columns, where_clause in indexes:
        try:
            sql = f"CREATE INDEX {index_name} ON {table}({columns}) {where_clause};"
            cursor.execute(sql)
            print(f"✓ Created index {index_name}")
        except psycopg2.errors.DuplicateTable:
            print(f"- Index {index_name} already exists")


def setup_database():
    """Main setup function"""
    print("Setting up Songbook Linkage System database...")
    
    try:
        conn = get_database_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create tables and columns
        create_matching_status_table(cursor)
        add_normalized_columns(cursor)
        add_dublin_core_columns(cursor)
        create_indexes(cursor)
        
        print("\n✅ Database setup completed successfully!")
        
        # Show current state
        cursor.execute("SELECT COUNT(*) FROM canonical_mele;")
        song_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM songbook_entries;")
        entry_count = cursor.fetchone()[0]
        
        print(f"📊 Current data: {song_count} songs, {entry_count} songbook entries")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        raise


if __name__ == "__main__":
    # Set password if not in environment
    if not os.getenv('PGPASSWORD'):
        raise ValueError("PGPASSWORD environment variable is required")
    setup_database()