#!/usr/bin/env python3
"""
Check the structure of the canonical_mele table to fix foreign key issue
"""
import os
import psycopg2

def get_db_config():
    return {
        'host': os.getenv('PGHOST', 'ep-young-silence-ad9wue88-pooler.c-2.us-east-1.aws.neon.tech'),
        'database': os.getenv('PGDATABASE', 'neondb'),
        'user': os.getenv('PGUSER', 'neondb_owner'),
        'password': os.getenv('PGPASSWORD'),
        'port': int(os.getenv('PGPORT', 5432)),
        'sslmode': 'require'
    }

def check_canonical_mele_structure():
    config = get_db_config()
    conn = psycopg2.connect(**config)
    
    try:
        with conn.cursor() as cursor:
            # Check the structure of canonical_mele table
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'canonical_mele' 
                ORDER BY ordinal_position
            """)
            
            print("📋 canonical_mele table structure:")
            columns = cursor.fetchall()
            for col_name, data_type, nullable, default in columns:
                print(f"   - {col_name}: {data_type} {'NULL' if nullable == 'YES' else 'NOT NULL'}")
                if default:
                    print(f"     Default: {default}")
            
            # Check for primary key
            cursor.execute("""
                SELECT column_name
                FROM information_schema.key_column_usage
                WHERE table_name = 'canonical_mele' 
                AND constraint_name LIKE '%pkey%'
            """)
            
            pk_cols = [row[0] for row in cursor.fetchall()]
            if pk_cols:
                print(f"\n🔑 Primary key: {', '.join(pk_cols)}")
            else:
                print("\n❌ No primary key found!")
            
            # Check for any existing foreign key constraints
            cursor.execute("""
                SELECT 
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name = 'canonical_mele'
            """)
            
            fk_constraints = cursor.fetchall()
            if fk_constraints:
                print("\n🔗 Existing foreign key constraints:")
                for constraint_name, column, ref_table, ref_column in fk_constraints:
                    print(f"   - {column} -> {ref_table}.{ref_column}")
            else:
                print("\n📝 No foreign key constraints found")
                
    finally:
        conn.close()

if __name__ == "__main__":
    check_canonical_mele_structure()