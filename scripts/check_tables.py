#!/usr/bin/env python3
"""
Check what tables exist in the database
"""
import os
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

def check_tables():
    """Check what tables exist in database"""
    
    database_url = get_database_url()
    if not database_url:
        print("❌ No database connection available")
        return
    
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        print("📋 Checking database tables...")
        
        # Get all tables
        cur.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename
        """)
        tables = cur.fetchall()
        
        print(f"📋 Found {len(tables)} tables:")
        for table in tables:
            # Get row count for each table
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cur.fetchone()[0]
                print(f"   - {table[0]}: {count} rows")
            except:
                print(f"   - {table[0]}: (could not count)")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_tables()