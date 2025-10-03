#!/usr/bin/env python3
"""
Create normalized verse tables in the database

This script creates the new normalized tables for verse storage,
replacing the verses_json column approach with proper relational tables.
"""

import os
import sys
from sqlalchemy import create_engine, text
from database import Base, get_database_url

def create_tables():
    """Create the new normalized verse tables"""
    
    # Get database connection
    DATABASE_URL = get_database_url()
    engine = create_engine(DATABASE_URL)
    
    print("Creating normalized verse tables...")
    
    try:
        # Create the new tables
        Base.metadata.create_all(engine, tables=[
            Base.metadata.tables['verses'],
            Base.metadata.tables['verse_lines'], 
            Base.metadata.tables['verse_processing_metadata']
        ])
        
        print("✅ Successfully created tables:")
        print("  - verses")
        print("  - verse_lines")
        print("  - verse_processing_metadata")
        
        # Add unique constraints
        with engine.connect() as conn:
            # Unique constraints for verses table
            conn.execute(text("""
                ALTER TABLE verses 
                ADD CONSTRAINT unique_mele_verse_id 
                UNIQUE (mele_source_id, verse_id)
            """))
            
            conn.execute(text("""
                ALTER TABLE verses 
                ADD CONSTRAINT unique_mele_verse_order 
                UNIQUE (mele_source_id, verse_order)
            """))
            
            # Unique constraints for verse_lines table
            conn.execute(text("""
                ALTER TABLE verse_lines 
                ADD CONSTRAINT unique_verse_line_id 
                UNIQUE (verse_id, line_id)
            """))
            
            conn.execute(text("""
                ALTER TABLE verse_lines 
                ADD CONSTRAINT unique_verse_line_number 
                UNIQUE (verse_id, line_number)
            """))
            
            conn.commit()
            
        print("✅ Successfully added unique constraints")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
        
    return True

def verify_tables():
    """Verify the tables were created correctly"""
    
    DATABASE_URL = get_database_url()
    engine = create_engine(DATABASE_URL)
    
    print("\nVerifying table creation...")
    
    try:
        with engine.connect() as conn:
            # Check that tables exist
            tables = ['verses', 'verse_lines', 'verse_processing_metadata']
            
            for table in tables:
                result = conn.execute(text(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = '{table}'
                    ORDER BY ordinal_position
                """))
                
                columns = result.fetchall()
                if columns:
                    print(f"\n✅ Table '{table}' created with {len(columns)} columns:")
                    for col in columns:
                        nullable = "NULL" if col.is_nullable == "YES" else "NOT NULL"
                        print(f"  - {col.column_name}: {col.data_type} {nullable}")
                else:
                    print(f"❌ Table '{table}' not found")
                    return False
                    
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        return False
        
    return True

if __name__ == "__main__":
    print("=== Creating Normalized Verse Tables ===")
    print("This will create new tables to replace verses_json storage.")
    print("The existing verses_json column will remain untouched for now.\n")
    
    # Check for required environment variables
    if not os.getenv('PGPASSWORD'):
        print("❌ Error: PGPASSWORD environment variable not set")
        sys.exit(1)
    
    # Create tables
    if create_tables():
        if verify_tables():
            print("\n🎉 Migration completed successfully!")
            print("\nNext steps:")
            print("1. Run the data migration script to populate new tables from verses_json")
            print("2. Update the comprehensive editor to use new tables")
            print("3. Update export scripts to read from new tables")
            print("4. Remove verses_json column after verification")
        else:
            print("\n❌ Table verification failed")
            sys.exit(1)
    else:
        print("\n❌ Table creation failed")
        sys.exit(1)