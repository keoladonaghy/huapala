#!/usr/bin/env python3
"""
Huapala FastAPI Backend for Railway

A FastAPI backend that serves Hawaiian music data from Neon PostgreSQL.
Acts as a bridge between GitHub Pages frontend and Neon database.
"""

import json
import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
# Note: database_validator.py import would go here when deployed

# Initialize FastAPI app
app = FastAPI(
    title="Huapala Hawaiian Music API",
    description="API bridge between GitHub Pages and Neon PostgreSQL",
    version="1.0.0"
)

# Add CORS middleware for GitHub Pages access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.github.io",  # GitHub Pages domains
        "http://localhost:*",   # Local development
        "*"  # Allow all for now - tighten in production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Database configuration - Railway env vars with Neon fallback
def get_db_config():
    return {
        'host': os.getenv('PGHOST', 'ep-young-silence-ad9wue88-pooler.c-2.us-east-1.aws.neon.tech'),
        'database': os.getenv('PGDATABASE', 'neondb'),
        'user': os.getenv('PGUSER', 'neondb_owner'),
        'password': os.getenv('PGPASSWORD'),
        'port': int(os.getenv('PGPORT', 5432)),
        'sslmode': 'require'
    }

def get_db_connection():
    """Get database connection with error handling"""
    try:
        config = get_db_config()
        config['connect_timeout'] = 10
        return psycopg2.connect(**config)
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Huapala Hawaiian Music API Bridge",
        "description": "Railway-hosted API connecting GitHub Pages to Neon PostgreSQL",
        "endpoints": {
            "/songs": "Get all songs (replaces songs-data.json)",
            "/songs/{song_id}": "Get specific song by ID",
            "/people/search": "Search for people by name",
            "/people/{person_id}": "Get specific person by ID",
            "/validation/summary": "Get validation session summaries",
            "/validation/review": "Get songs needing manual review",
            "/validation/songs/{song_id}": "Get validation details for specific song",
            "/health": "Health check endpoint"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {"status": "healthy", "database": "connected", "host": "railway+neon"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database health check failed: {str(e)}")

@app.get("/songs")
async def get_songs(
    search: Optional[str] = Query(None, description="Search term for filtering songs"),
    limit: Optional[int] = Query(100, ge=1, le=1000)
):
    """Get all songs - replaces the static songs-data.json file"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Same query as export_to_web.py to maintain compatibility
        base_query = """
        SELECT 
            cm.canonical_mele_id,
            cm.canonical_title_hawaiian,
            cm.canonical_title_english,
            cm.primary_composer,
            cm.primary_lyricist,
            cm.estimated_composition_date,
            cm.cultural_significance_notes,
            ms.composer,
            ms.translator,
            ms.hawaiian_editor,
            ms.source_file,
            ms.source_publication,
            ms.copyright_info,
            ms.verses_json,
            ms.song_type,
            ms.structure_type,
            ms.primary_location,
            ms.island,
            ms.themes,
            ms.mele_type,
            ms.cultural_elements,
            COUNT(mm.id) as youtube_count,
            ARRAY_AGG(mm.url) FILTER (WHERE mm.url IS NOT NULL) as youtube_urls
        FROM canonical_mele cm
        LEFT JOIN mele_sources ms ON cm.canonical_mele_id = ms.canonical_mele_id
        LEFT JOIN mele_media mm ON cm.canonical_mele_id = mm.canonical_mele_id
        """
        
        # Add search filtering if provided
        where_clause = ""
        params = []
        if search:
            where_clause = """
            WHERE (
                cm.canonical_title_hawaiian ILIKE %s OR
                cm.canonical_title_english ILIKE %s OR
                cm.primary_composer ILIKE %s OR
                ms.primary_location ILIKE %s OR
                ms.island ILIKE %s
            )
            """
            search_term = f"%{search}%"
            params = [search_term] * 5
        
        group_clause = """
        GROUP BY 
            cm.canonical_mele_id, cm.canonical_title_hawaiian, cm.canonical_title_english,
            cm.primary_composer, cm.primary_lyricist, cm.estimated_composition_date,
            cm.cultural_significance_notes, ms.composer, ms.translator, ms.hawaiian_editor,
            ms.source_file, ms.source_publication, ms.copyright_info, ms.verses_json,
            ms.song_type, ms.structure_type, ms.primary_location, ms.island, ms.themes, ms.mele_type, ms.cultural_elements
        ORDER BY cm.canonical_title_hawaiian
        LIMIT %s
        """
        
        query = base_query + where_clause + group_clause
        params.append(limit)
        
        cur.execute(query, params)
        rows = cur.fetchall()
        
        # Process data exactly like export_to_web.py for compatibility
        songs_data = []
        for row in rows:
            song = dict(row)
            
            # Parse JSON fields
            if song['verses_json']:
                try:
                    song['verses'] = json.loads(song['verses_json'])
                except:
                    song['verses'] = []
            else:
                song['verses'] = []
            
            # Clean up None values and empty arrays
            if song['youtube_urls'] and song['youtube_urls'][0] is None:
                song['youtube_urls'] = []
            elif not song['youtube_urls']:
                song['youtube_urls'] = []
                
            if song['youtube_count'] == 0:
                song['youtube_count'] = None
                
            # Remove the raw JSON field
            del song['verses_json']
            
            songs_data.append(song)
        
        return songs_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching songs: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/songs/{song_id}")
async def get_song(song_id: str):
    """Get a specific song by canonical_mele_id"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = """
        SELECT 
            cm.canonical_mele_id,
            cm.canonical_title_hawaiian,
            cm.canonical_title_english,
            cm.primary_composer,
            cm.primary_lyricist,
            cm.estimated_composition_date,
            cm.cultural_significance_notes,
            ms.composer,
            ms.translator,
            ms.hawaiian_editor,
            ms.source_file,
            ms.source_publication,
            ms.copyright_info,
            ms.verses_json,
            ms.song_type,
            ms.structure_type,
            ms.primary_location,
            ms.island,
            ms.themes,
            ms.mele_type,
            ms.cultural_elements,
            COUNT(mm.id) as youtube_count,
            ARRAY_AGG(mm.url) FILTER (WHERE mm.url IS NOT NULL) as youtube_urls
        FROM canonical_mele cm
        LEFT JOIN mele_sources ms ON cm.canonical_mele_id = ms.canonical_mele_id
        LEFT JOIN mele_media mm ON cm.canonical_mele_id = mm.canonical_mele_id
        WHERE cm.canonical_mele_id = %s
        GROUP BY 
            cm.canonical_mele_id, cm.canonical_title_hawaiian, cm.canonical_title_english,
            cm.primary_composer, cm.primary_lyricist, cm.estimated_composition_date,
            cm.cultural_significance_notes, ms.composer, ms.translator, ms.hawaiian_editor,
            ms.source_file, ms.source_publication, ms.copyright_info, ms.verses_json,
            ms.song_type, ms.structure_type, ms.primary_location, ms.island, ms.themes, ms.mele_type, ms.cultural_elements
        """
        
        cur.execute(query, (song_id,))
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Song with ID {song_id} not found")
        
        # Process data (same as export script)
        song = dict(row)
        
        # Parse JSON fields
        if song['verses_json']:
            try:
                song['verses'] = json.loads(song['verses_json'])
            except:
                song['verses'] = []
        else:
            song['verses'] = []
        
        # Clean up None values and empty arrays
        if song['youtube_urls'] and song['youtube_urls'][0] is None:
            song['youtube_urls'] = []
        elif not song['youtube_urls']:
            song['youtube_urls'] = []
            
        if song['youtube_count'] == 0:
            song['youtube_count'] = None
            
        # Remove the raw JSON field
        del song['verses_json']
        
        return song
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching song: {str(e)}")
    finally:
        cur.close()
        conn.close()

# People API endpoints
@app.get("/people/search")
async def search_people(name: str = Query(..., description="Name to search for")):
    """Search for people by name (exact or fuzzy match)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # First try exact match, then fuzzy match
        query = """
        SELECT person_id, full_name, display_name, place_of_birth, 
               primary_influence_location, hawaiian_speaker, birth_date, death_date,
               cultural_background, biographical_notes, roles, primary_role, 
               specialties, notable_works, awards_honors, verification_status
        FROM people 
        WHERE full_name ILIKE %s 
           OR display_name ILIKE %s
           OR full_name ILIKE %s
        ORDER BY 
            CASE 
                WHEN full_name ILIKE %s THEN 1
                WHEN display_name ILIKE %s THEN 2
                ELSE 3
            END
        LIMIT 1
        """
        
        exact_match = f"{name}"
        fuzzy_match = f"%{name}%"
        
        cur.execute(query, (exact_match, exact_match, fuzzy_match, exact_match, exact_match))
        row = cur.fetchone()
        
        if not row:
            return None
            
        person = dict(row)
        return person
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching people: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/people/{person_id}")
async def get_person(person_id: str):
    """Get a specific person by person_id"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = """
        SELECT person_id, full_name, display_name, place_of_birth, 
               primary_influence_location, hawaiian_speaker, birth_date, death_date,
               cultural_background, biographical_notes, roles, primary_role, 
               specialties, notable_works, awards_honors, verification_status,
               places_of_hawaiian_influence, source_references
        FROM people 
        WHERE person_id = %s
        """
        
        cur.execute(query, (person_id,))
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Person with ID {person_id} not found")
            
        person = dict(row)
        return person
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching person: {str(e)}")
    finally:
        cur.close()
        conn.close()

# Validation API endpoints
@app.get("/validation/summary")
async def get_validation_summary(session_id: Optional[int] = Query(None)):
    """Get validation session summaries"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        if session_id:
            cur.execute("SELECT * FROM validation_summary WHERE session_id = %s", (session_id,))
            result = cur.fetchone()
            return dict(result) if result else {}
        else:
            cur.execute("SELECT * FROM validation_summary ORDER BY started_at DESC LIMIT 10")
            return [dict(row) for row in cur.fetchall()]
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching validation summary: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/validation/review")
async def get_songs_needing_review():
    """Get all songs that require manual review"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("SELECT * FROM songs_needing_review ORDER BY data_quality_score ASC")
        return [dict(row) for row in cur.fetchall()]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching songs for review: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/validation/songs/{song_id}")
async def get_song_validation_details(song_id: int):
    """Get detailed validation information for a specific song"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("SELECT * FROM get_song_validation_details(%s)", (song_id,))
        result = cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"No validation data found for song {song_id}")
            
        return dict(result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching validation details: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/validation/sessions")
async def get_validation_sessions():
    """Get all validation sessions"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT id, session_name, started_at, completed_at, total_songs, 
                   songs_processed, songs_flagged, average_quality_score, status
            FROM validation_sessions 
            ORDER BY started_at DESC
        """)
        return [dict(row) for row in cur.fetchall()]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching validation sessions: {str(e)}")
    finally:
        cur.close()
        conn.close()

# Pydantic models for songbook entries
class SongbookEntryCreate(BaseModel):
    printed_song_title: str
    eng_title_transl: Optional[str] = None
    modern_song_title: Optional[str] = None
    scripped_song_title: Optional[str] = None
    song_title: Optional[str] = None
    songbook_name: str
    page: Optional[int] = None
    pub_year: Optional[int] = None
    diacritics: Optional[str] = None
    composer: Optional[str] = None
    additional_information: Optional[str] = None
    email_address: Optional[str] = None

class SongbookEntryUpdate(BaseModel):
    printed_song_title: Optional[str] = None
    eng_title_transl: Optional[str] = None
    modern_song_title: Optional[str] = None
    scripped_song_title: Optional[str] = None
    song_title: Optional[str] = None
    songbook_name: Optional[str] = None
    page: Optional[int] = None
    pub_year: Optional[int] = None
    diacritics: Optional[str] = None
    composer: Optional[str] = None
    additional_information: Optional[str] = None
    email_address: Optional[str] = None

# Songbook Entries API endpoints
@app.get("/api/songbook-entries")
async def get_songbook_entries(
    limit: int = Query(100, description="Maximum number of entries to return"),
    offset: int = Query(0, description="Number of entries to skip"),
    songbook_name: Optional[str] = Query(None, description="Filter by songbook name"),
    composer: Optional[str] = Query(None, description="Filter by composer"),
    pub_year_min: Optional[int] = Query(None, description="Minimum publication year"),
    pub_year_max: Optional[int] = Query(None, description="Maximum publication year"),
    search: Optional[str] = Query(None, description="Search in titles and composer")
):
    """Get songbook entries with optional filtering and pagination"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Build WHERE clauses
        where_clauses = []
        params = []
        
        if songbook_name:
            where_clauses.append("songbook_name = %s")
            params.append(songbook_name)
            
        if composer:
            where_clauses.append("composer ILIKE %s")
            params.append(f"%{composer}%")
            
        if pub_year_min:
            where_clauses.append("pub_year >= %s")
            params.append(pub_year_min)
            
        if pub_year_max:
            where_clauses.append("pub_year <= %s")
            params.append(pub_year_max)
            
        if search:
            where_clauses.append("""
                (printed_song_title ILIKE %s 
                 OR eng_title_transl ILIKE %s 
                 OR modern_song_title ILIKE %s 
                 OR composer ILIKE %s)
            """)
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param, search_param])
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        query = f"""
            SELECT id, timestamp, printed_song_title, eng_title_transl, modern_song_title,
                   scripped_song_title, song_title, songbook_name, page, pub_year,
                   diacritics, composer, additional_information, email_address,
                   canonical_mele_id, created_at, updated_at
            FROM songbook_entries
            {where_sql}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        
        params.extend([limit, offset])
        cur.execute(query, params)
        
        entries = [dict(row) for row in cur.fetchall()]
        return entries
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching songbook entries: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/api/songbook-entries/{entry_id}")
async def get_songbook_entry(entry_id: int):
    """Get a single songbook entry by ID"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT id, timestamp, printed_song_title, eng_title_transl, modern_song_title,
                   scripped_song_title, song_title, songbook_name, page, pub_year,
                   diacritics, composer, additional_information, email_address,
                   canonical_mele_id, created_at, updated_at
            FROM songbook_entries
            WHERE id = %s
        """, (entry_id,))
        
        entry = cur.fetchone()
        if not entry:
            raise HTTPException(status_code=404, detail="Songbook entry not found")
            
        return dict(entry)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching songbook entry: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.post("/api/songbook-entries")
async def create_songbook_entry(entry: SongbookEntryCreate):
    """Create a new songbook entry"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            INSERT INTO songbook_entries (
                printed_song_title, eng_title_transl, modern_song_title,
                scripped_song_title, song_title, songbook_name, page, pub_year,
                diacritics, composer, additional_information, email_address
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, timestamp, printed_song_title, eng_title_transl, modern_song_title,
                      scripped_song_title, song_title, songbook_name, page, pub_year,
                      diacritics, composer, additional_information, email_address,
                      canonical_mele_id, created_at, updated_at
        """, (
            entry.printed_song_title,
            entry.eng_title_transl,
            entry.modern_song_title,
            entry.scripped_song_title,
            entry.song_title,
            entry.songbook_name,
            entry.page,
            entry.pub_year,
            entry.diacritics,
            entry.composer,
            entry.additional_information,
            entry.email_address
        ))
        
        created_entry = dict(cur.fetchone())
        conn.commit()
        return created_entry
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating songbook entry: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.put("/api/songbook-entries/{entry_id}")
async def update_songbook_entry(entry_id: int, entry: SongbookEntryUpdate):
    """Update an existing songbook entry"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Build update fields dynamically
        update_fields = []
        params = []
        
        entry_dict = entry.dict(exclude_unset=True)
        for field, value in entry_dict.items():
            update_fields.append(f"{field} = %s")
            params.append(value)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(entry_id)
        
        query = f"""
            UPDATE songbook_entries 
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE id = %s
            RETURNING id, timestamp, printed_song_title, eng_title_transl, modern_song_title,
                      scripped_song_title, song_title, songbook_name, page, pub_year,
                      diacritics, composer, additional_information, email_address,
                      canonical_mele_id, created_at, updated_at
        """
        
        cur.execute(query, params)
        updated_entry = cur.fetchone()
        
        if not updated_entry:
            raise HTTPException(status_code=404, detail="Songbook entry not found")
        
        conn.commit()
        return dict(updated_entry)
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating songbook entry: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.delete("/api/songbook-entries/{entry_id}")
async def delete_songbook_entry(entry_id: int):
    """Delete a songbook entry"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM songbook_entries WHERE id = %s", (entry_id,))
        
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Songbook entry not found")
        
        conn.commit()
        return {"message": "Songbook entry deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting songbook entry: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/api/songbook-names")
async def get_songbook_names():
    """Get unique songbook names for dropdown lists"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT DISTINCT songbook_name 
            FROM songbook_entries 
            WHERE songbook_name IS NOT NULL 
            ORDER BY songbook_name
        """)
        
        names = [row[0] for row in cur.fetchall()]
        return names
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching songbook names: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/api/songbook-stats")
async def get_songbook_stats():
    """Get statistics about songbook entries"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get basic stats
        cur.execute("""
            SELECT 
                COUNT(*) as total_entries,
                COUNT(DISTINCT songbook_name) as unique_songbooks,
                COUNT(DISTINCT composer) as unique_composers,
                COUNT(page) as entries_with_pages
            FROM songbook_entries
        """)
        
        stats = dict(cur.fetchone())
        
        # Get entries by decade
        cur.execute("""
            SELECT 
                CONCAT(FLOOR(pub_year/10)*10, 's') as decade,
                COUNT(*) as count
            FROM songbook_entries 
            WHERE pub_year IS NOT NULL
            GROUP BY FLOOR(pub_year/10)*10
            ORDER BY FLOOR(pub_year/10)*10
        """)
        
        decades = [dict(row) for row in cur.fetchall()]
        stats['entries_by_decade'] = decades
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching songbook stats: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/api/canonical-mele")
async def get_canonical_mele(
    limit: int = Query(100, description="Maximum number of songs to return"),
    search: Optional[str] = Query(None, description="Search in titles and composer")
):
    """Get canonical songs for reference (read-only)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        where_sql = ""
        params = []
        
        if search:
            where_sql = """
                WHERE canonical_title_hawaiian ILIKE %s 
                   OR canonical_title_english ILIKE %s 
                   OR primary_composer ILIKE %s
            """
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        query = f"""
            SELECT canonical_mele_id, canonical_title_hawaiian, 
                   canonical_title_english, primary_composer
            FROM canonical_mele
            {where_sql}
            ORDER BY canonical_title_hawaiian
            LIMIT %s
        """
        
        params.append(limit)
        cur.execute(query, params)
        
        songs = [dict(row) for row in cur.fetchall()]
        return songs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching canonical songs: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/api/people")
async def get_people(
    limit: int = Query(100, description="Maximum number of people to return"),
    search: Optional[str] = Query(None, description="Search in names"),
    role: Optional[str] = Query(None, description="Filter by role")
):
    """Get people for reference (read-only)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        where_clauses = []
        params = []
        
        if search:
            where_clauses.append("(full_name ILIKE %s OR display_name ILIKE %s)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param])
            
        if role:
            where_clauses.append("roles @> %s")
            params.append(json.dumps([role]))
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        query = f"""
            SELECT person_id, full_name as name, roles
            FROM people
            {where_sql}
            ORDER BY full_name
            LIMIT %s
        """
        
        params.append(limit)
        cur.execute(query, params)
        
        people = [dict(row) for row in cur.fetchall()]
        return people
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching people: {str(e)}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))