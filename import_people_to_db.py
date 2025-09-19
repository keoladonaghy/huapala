#!/usr/bin/env python3
"""
Import people JSON data into the PostgreSQL database
"""
import json
import os
import psycopg2
from pathlib import Path
from datetime import datetime
import re

def get_db_config():
    return {
        'host': os.getenv('PGHOST', 'ep-young-silence-ad9wue88-pooler.c-2.us-east-1.aws.neon.tech'),
        'database': os.getenv('PGDATABASE', 'neondb'),
        'user': os.getenv('PGUSER', 'neondb_owner'),
        'password': os.getenv('PGPASSWORD', 'npg_Ic2Qq1ErOykl'),
        'port': int(os.getenv('PGPORT', 5432)),
        'sslmode': 'require'
    }

def parse_date(date_str):
    """Parse various date formats and return PostgreSQL-compatible date string or None"""
    if not date_str or date_str == "null":
        return None
    
    # If it's just a year like "1987"
    if re.match(r'^\d{4}$', str(date_str)):
        return f"{date_str}-01-01"
    
    # Try to parse common date formats
    date_formats = [
        "%B %d, %Y",  # "August 12, 1892"
        "%Y-%m-%d",   # "1892-08-12"
        "%m/%d/%Y",   # "08/12/1892"
        "%d/%m/%Y",   # "12/08/1892"
    ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(str(date_str), fmt)
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # If we can't parse it, return None
    print(f"   ⚠️  Could not parse date: {date_str}")
    return None

def import_people_to_db():
    """Import all people JSON files into the database"""
    config = get_db_config()
    conn = psycopg2.connect(**config)
    
    json_dir = Path("data/people_json")
    
    if not json_dir.exists():
        print(f"❌ Directory {json_dir} does not exist!")
        return False
    
    json_files = list(json_dir.glob("*.json"))
    print(f"📁 Found {len(json_files)} JSON files to import")
    
    imported_count = 0
    error_count = 0
    
    for json_file in json_files:
        try:
            with conn.cursor() as cursor:
                print(f"📥 Processing {json_file.name}...")
                
                with open(json_file, 'r', encoding='utf-8') as f:
                    person_data = json.load(f)
                    
                    # Insert into people table
                    cursor.execute("""
                        INSERT INTO people (
                            person_id, full_name, display_name,
                            place_of_birth, places_of_hawaiian_influence, primary_influence_location,
                            hawaiian_speaker, birth_date, death_date, cultural_background,
                            biographical_notes, roles, primary_role, specialties,
                            active_period_start, active_period_end, notable_works, awards_honors,
                            composition_count, translation_count, editing_count, performance_count,
                            total_contributions, most_frequent_role, last_activity_date,
                            source_references, verification_status, last_verified_date
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        ON CONFLICT (person_id) DO UPDATE SET
                            full_name = EXCLUDED.full_name,
                            display_name = EXCLUDED.display_name,
                            place_of_birth = EXCLUDED.place_of_birth,
                            places_of_hawaiian_influence = EXCLUDED.places_of_hawaiian_influence,
                            primary_influence_location = EXCLUDED.primary_influence_location,
                            hawaiian_speaker = EXCLUDED.hawaiian_speaker,
                            birth_date = EXCLUDED.birth_date,
                            death_date = EXCLUDED.death_date,
                            cultural_background = EXCLUDED.cultural_background,
                            biographical_notes = EXCLUDED.biographical_notes,
                            roles = EXCLUDED.roles,
                            primary_role = EXCLUDED.primary_role,
                            specialties = EXCLUDED.specialties,
                            active_period_start = EXCLUDED.active_period_start,
                            active_period_end = EXCLUDED.active_period_end,
                            notable_works = EXCLUDED.notable_works,
                            awards_honors = EXCLUDED.awards_honors,
                            source_references = EXCLUDED.source_references,
                            verification_status = EXCLUDED.verification_status,
                            last_verified_date = EXCLUDED.last_verified_date,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        person_data['person_id'],
                        person_data['full_name'],
                        person_data.get('display_name'),
                        person_data.get('place_of_birth'),
                        json.dumps(person_data.get('places_of_hawaiian_influence', [])),
                        person_data.get('primary_influence_location'),
                        person_data.get('hawaiian_speaker'),
                        parse_date(person_data.get('birth_date')),
                        parse_date(person_data.get('death_date')),
                        person_data.get('cultural_background'),
                        person_data.get('biographical_notes'),
                        person_data.get('roles', []),
                        person_data.get('primary_role'),
                        person_data.get('specialties', []),
                        person_data.get('active_period_start'),
                        person_data.get('active_period_end'),
                        person_data.get('notable_works', []),
                        person_data.get('awards_honors', []),
                        person_data.get('composition_count', 0),
                        person_data.get('translation_count', 0),
                        person_data.get('editing_count', 0),
                        person_data.get('performance_count', 0),
                        person_data.get('total_contributions', 0),
                        person_data.get('most_frequent_role'),
                        person_data.get('last_activity_date'),
                        json.dumps(person_data.get('source_references', {})),
                        person_data.get('verification_status', 'unverified'),
                        parse_date(person_data.get('last_verified_date'))
                    ))
                
                # Commit this person's data
                conn.commit()
                imported_count += 1
                print(f"   ✅ Successfully imported {person_data['full_name']}")
                
        except Exception as e:
            error_count += 1
            print(f"   ❌ Error importing {json_file.name}: {e}")
            conn.rollback()  # Rollback just this person's transaction
    
    try:
        with conn.cursor() as cursor:
            print(f"\n🎉 Import completed!")
            print(f"   ✅ Successfully imported: {imported_count} people")
            if error_count > 0:
                print(f"   ❌ Errors encountered: {error_count} files")
            
            # Show summary
            cursor.execute("SELECT COUNT(*) FROM people")
            total_people = cursor.fetchone()[0]
            print(f"   📊 Total people in database: {total_people}")
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    finally:
        conn.close()
    
    return error_count == 0

def show_imported_people():
    """Show a summary of imported people"""
    config = get_db_config()
    conn = psycopg2.connect(**config)
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT person_id, full_name, primary_role, 
                       array_length(roles, 1) as role_count,
                       array_length(notable_works, 1) as work_count
                FROM people 
                ORDER BY full_name
            """)
            
            print("\n📋 Imported People Summary:")
            print("=" * 80)
            for row in cursor.fetchall():
                person_id, full_name, primary_role, role_count, work_count = row
                roles_text = f"{role_count} role(s)" if role_count else "no roles"
                works_text = f"{work_count} work(s)" if work_count else "no notable works"
                print(f"{full_name:30} | {primary_role or 'N/A':15} | {roles_text} | {works_text}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Starting people data import...")
    success = import_people_to_db()
    
    if success:
        show_imported_people()
        print("\n✅ All people data successfully imported!")
    else:
        print("\n❌ Import completed with errors. Check the output above.")