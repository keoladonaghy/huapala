#!/usr/bin/env python3
"""
Migrate verse data from JSON to normalized tables

This script reads verses_json from mele_sources and populates
the new normalized verse tables.
"""

import os
import sys
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import get_database_url, MeleSources, Verses, VerseLines, VerseProcessingMetadata

def migrate_verses_data():
    """Migrate all verse data from JSON to normalized tables"""
    
    # Database setup
    DATABASE_URL = get_database_url()
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Get all mele_sources with verses_json data
        sources = session.query(MeleSources).filter(MeleSources.verses_json.isnot(None)).all()
        
        print(f"Found {len(sources)} songs with verse data to migrate")
        
        migrated_count = 0
        error_count = 0
        
        for source in sources:
            try:
                print(f"\nMigrating: {source.id}")
                
                # Parse the verses_json
                verses_data = source.verses_json
                
                # Handle both string and dict cases (from corruption issues)
                if isinstance(verses_data, str):
                    try:
                        verses_data = json.loads(verses_data)
                    except json.JSONDecodeError:
                        print(f"  ❌ Invalid JSON format for {source.id}")
                        error_count += 1
                        continue
                
                # Extract verses and processing metadata
                verses_list = verses_data.get('verses', [])
                processing_metadata = verses_data.get('processing_metadata', {})
                
                # Skip if no verses
                if not verses_list:
                    print(f"  ⚠️  No verses found for {source.id}")
                    continue
                
                # Create processing metadata record
                if processing_metadata or True:  # Always create a record
                    metadata_record = VerseProcessingMetadata(
                        mele_source_id=source.id,
                        processing_notes=processing_metadata.get('notes'),
                        validation_status=processing_metadata.get('status'),
                        last_processed_at=datetime.utcnow(),
                        processor_version='migration_script_v1'
                    )
                    session.add(metadata_record)
                
                # Process each verse - assign sequential order and unique IDs
                for index, verse_data in enumerate(verses_list, 1):
                    # Ensure unique verse_id by appending index if needed
                    original_verse_id = verse_data.get('id', f"v{verse_data.get('number', 1)}")
                    verse_id = f"{original_verse_id}_{index}" if original_verse_id else f"verse_{index}"
                    
                    # Create verse record
                    verse_record = Verses(
                        mele_source_id=source.id,
                        verse_id=verse_id,
                        verse_type=verse_data.get('type', 'verse'),
                        verse_number=verse_data.get('number'),
                        verse_order=index,  # Use sequential index to avoid conflicts
                        label=verse_data.get('label')
                    )
                    session.add(verse_record)
                    session.flush()  # Get the verse ID
                    
                    # Process lines within the verse
                    lines_data = verse_data.get('lines', [])
                    for line_data in lines_data:
                        line_record = VerseLines(
                            verse_id=verse_record.id,
                            line_id=line_data.get('id', f"{verse_record.verse_id}.{line_data.get('line_number', 1)}"),
                            line_number=line_data.get('line_number', 1),
                            hawaiian_text=line_data.get('hawaiian_text'),
                            english_text=line_data.get('english_text'),
                            is_bilingual=line_data.get('is_bilingual', False)
                        )
                        session.add(line_record)
                    
                    print(f"  ✅ Migrated verse {verse_record.verse_id} with {len(lines_data)} lines")
                
                # Commit this song's data
                session.commit()
                migrated_count += 1
                print(f"  ✅ Successfully migrated {source.id}")
                
            except Exception as e:
                print(f"  ❌ Error migrating {source.id}: {e}")
                session.rollback()
                error_count += 1
                continue
        
        print(f"\n=== Migration Summary ===")
        print(f"✅ Successfully migrated: {migrated_count} songs")
        print(f"❌ Errors: {error_count} songs")
        
        return error_count == 0
        
    except Exception as e:
        print(f"❌ Fatal error during migration: {e}")
        session.rollback()
        return False
        
    finally:
        session.close()

def verify_migration():
    """Verify the migration was successful"""
    
    DATABASE_URL = get_database_url()
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Count records in each table
        verse_count = session.query(Verses).count()
        line_count = session.query(VerseLines).count()
        metadata_count = session.query(VerseProcessingMetadata).count()
        
        print(f"\n=== Migration Verification ===")
        print(f"📊 Verses: {verse_count}")
        print(f"📊 Lines: {line_count}")
        print(f"📊 Processing metadata: {metadata_count}")
        
        # Check for data integrity
        orphaned_lines = session.query(VerseLines).filter(
            ~VerseLines.verse_id.in_(session.query(Verses.id))
        ).count()
        
        if orphaned_lines > 0:
            print(f"⚠️  Found {orphaned_lines} orphaned lines")
            return False
        
        print("✅ Data integrity check passed")
        return True
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False
        
    finally:
        session.close()

if __name__ == "__main__":
    print("=== Migrating Verse Data to Normalized Tables ===")
    print("This will read verses_json and populate the new normalized tables.\n")
    
    # Check for required environment variables
    if not os.getenv('PGPASSWORD'):
        print("❌ Error: PGPASSWORD environment variable not set")
        sys.exit(1)
    
    # Run migration
    if migrate_verses_data():
        if verify_migration():
            print("\n🎉 Migration completed successfully!")
            print("\nNext steps:")
            print("1. Test the comprehensive editor with new tables")
            print("2. Update export scripts to read from new tables")
            print("3. Verify all functionality works correctly")
            print("4. Remove verses_json column after full verification")
        else:
            print("\n❌ Migration verification failed")
            sys.exit(1)
    else:
        print("\n❌ Migration failed")
        sys.exit(1)