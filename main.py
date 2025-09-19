#!/usr/bin/env python3
"""
Huapala FastAPI Backend for Railway

A FastAPI backend that serves Hawaiian music data from Neon PostgreSQL.
Acts as a bridge between GitHub Pages frontend and Neon database.
"""

import json
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
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
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Database configuration - Railway env vars with Neon fallback
def get_db_config():
    return {
        'host': os.getenv('PGHOST', 'ep-young-silence-ad9wue88-pooler.c-2.us-east-1.aws.neon.tech'),
        'database': os.getenv('PGDATABASE', 'neondb'),
        'user': os.getenv('PGUSER', 'neondb_owner'),
        'password': os.getenv('PGPASSWORD', 'npg_Ic2Qq1ErOykl'),
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
            ms.primary_location, ms.island, ms.themes, ms.mele_type, ms.cultural_elements
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
            ms.primary_location, ms.island, ms.themes, ms.mele_type, ms.cultural_elements
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))