#!/usr/bin/env python3
"""
Check what validation tables exist in the database
"""
import os
import psycopg2

def get_db_config():
    return {
        'host': os.getenv('PGHOST', 'ep-young-silence-ad9wue88-pooler.c-2.us-east-1.aws.neon.tech'),
        'database': os.getenv('PGDATABASE', 'neondb'),
        'user': os.getenv('PGUSER', 'neondb_owner'),
        'password': os.getenv('PGPASSWORD', 'npg_Ic2Qq1ErOykl'),
        'port': int(os.getenv('PGPORT', 5432)),
        'sslmode': 'require'
    }

def check_tables():
    config = get_db_config()
    conn = psycopg2.connect(**config)
    
    try:
        with conn.cursor() as cursor:
            # Check what tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            print("📋 Existing tables in database:")
            for table in tables:
                print(f"   - {table}")
            
            # Check specifically for validation tables
            validation_tables = ['validation_sessions', 'song_validations', 'validation_issues']
            missing_tables = [t for t in validation_tables if t not in tables]
            
            if missing_tables:
                print(f"\n❌ Missing validation tables: {missing_tables}")
                print("   The validation schema was not fully applied.")
                return False
            else:
                print("\n✅ All validation tables exist!")
                return True
                
    finally:
        conn.close()

if __name__ == "__main__":
    check_tables()