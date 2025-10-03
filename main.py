#!/usr/bin/env python3
"""
Huapala FastAPI Backend for Railway

A FastAPI backend that serves Hawaiian music data from Neon PostgreSQL.
Acts as a bridge between GitHub Pages frontend and Neon database.
"""

import json
import os
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Body, Request, Response, Cookie, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import secrets
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from auth import get_db_connection, get_db_config

# Load environment variables from .env file
load_dotenv()

# SQLAdmin imports removed
from database import engine, CanonicalMele, MeleSources, MeleMedia, People, SongbookEntries, ValidationSessions, Verses, VerseLines, VerseProcessingMetadata, SessionLocal

# Comprehensive song editor models
from models.song_models import (
    ComprehensiveSongModel, FormProcessingModel, ValidationResult, 
    validate_song_data, create_backup_filename
)
# Note: database_validator.py import would go here when deployed

# Initialize FastAPI app
app = FastAPI(
    title="Huapala Hawaiian Music API",
    description="API bridge between GitHub Pages and Neon PostgreSQL",
    version="1.0.0"
)

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# SQLAdmin authentication backend removed

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

# Simple session management
sessions = {}
SESSION_TIMEOUT = timedelta(hours=2)
ADMIN_USERNAME = "kahu"
ADMIN_PASSWORD = "huapala2025!"

def generate_session_token():
    return secrets.token_urlsafe(32)

def create_session(username: str) -> str:
    token = generate_session_token()
    sessions[token] = {
        "username": username,
        "created_at": datetime.now(),
        "last_accessed": datetime.now()
    }
    return token

def validate_session(token: str) -> bool:
    if not token or token not in sessions:
        return False
    
    session = sessions[token]
    if datetime.now() - session["last_accessed"] > SESSION_TIMEOUT:
        del sessions[token]
        return False
    
    session["last_accessed"] = datetime.now()
    return True

def require_auth(request: Request):
    """Dependency to require authentication for admin routes"""
    token = request.cookies.get("admin_session")
    if not validate_session(token):
        raise HTTPException(status_code=401, detail="Authentication required")
    return token

def check_admin_auth(request: Request):
    """Check authentication and return RedirectResponse if not authenticated"""
    token = request.cookies.get("admin_session")
    if not validate_session(token):
        return RedirectResponse(url="/admin/login", status_code=302)
    return None  # No redirect needed

# SQLAdmin ModelViews removed

# Database configuration now imported from auth.py

def get_db_connection_fastapi():
    """Get database connection with FastAPI-compatible error handling"""
    try:
        return get_db_connection()
    except ConnectionError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the home page"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Home page not found")

@app.get("/index.html", response_class=HTMLResponse)
async def index_page():
    """Serve the home page at /index.html"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Home page not found")

@app.get("/song.html", response_class=HTMLResponse)
async def song_page():
    """Serve the individual song page"""
    try:
        with open("song.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Song page not found")

@app.get("/api", response_class=Response)
async def api_info():
    """API information endpoint"""
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
        conn = get_db_connection_fastapi()
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
    conn = get_db_connection_fastapi()
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
            ms.source_file, ms.source_publication, ms.copyright_info,
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
            
            # For the songs list, we don't include verse content for performance
            # Individual songs load verses from the /songs/{song_id} endpoint
            song['verses'] = []
            
            # Clean up None values and empty arrays
            if song['youtube_urls'] and song['youtube_urls'][0] is None:
                song['youtube_urls'] = []
            elif not song['youtube_urls']:
                song['youtube_urls'] = []
                
            if song['youtube_count'] == 0:
                song['youtube_count'] = None
            
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
    try:
        # Use the same function that works in the comprehensive editor
        song_data = get_comprehensive_song_data(song_id)
        
        if not song_data:
            raise HTTPException(status_code=404, detail=f"Song with ID {song_id} not found")
        
        # The function already returns a dict, so use it directly
        song_dict = song_data
        
        # The verses structure should already be in the right format from get_comprehensive_song_data()
        # Just ensure we have the verses in the expected format
        if not song_dict.get('verses'):
            song_dict['verses'] = []
        
        # Get media links from database - need a separate DB session for this
        db = SessionLocal()
        try:
            media_links = db.query(MeleMedia).filter(MeleMedia.canonical_mele_id == song_id).all()
            youtube_urls = [media.url for media in media_links if media.url]
            song_dict['youtube_urls'] = youtube_urls
            song_dict['youtube_count'] = len(youtube_urls) if youtube_urls else None
        finally:
            db.close()
        
        # Remove None values and system fields that frontend doesn't need
        fields_to_remove = ['created_at', 'updated_at', 'media_links']
        for field in fields_to_remove:
            if field in song_dict:
                del song_dict[field]
        
        print(f"DEBUG API: Returning song data for {song_id} with {len(song_dict.get('verses', []))} verses")
        return song_dict
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR API: Failed to fetch song {song_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching song: {str(e)}")

# People API endpoints
@app.get("/people/search")
async def search_people(name: str = Query(..., description="Name to search for")):
    """Search for people by name (exact or fuzzy match)"""
    conn = get_db_connection_fastapi()
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
    conn = get_db_connection_fastapi()
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
    conn = get_db_connection_fastapi()
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
    conn = get_db_connection_fastapi()
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
    conn = get_db_connection_fastapi()
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
    conn = get_db_connection_fastapi()
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
    conn = get_db_connection_fastapi()
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
    conn = get_db_connection_fastapi()
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
    conn = get_db_connection_fastapi()
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
    conn = get_db_connection_fastapi()
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
    conn = get_db_connection_fastapi()
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
    conn = get_db_connection_fastapi()
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
    conn = get_db_connection_fastapi()
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
    conn = get_db_connection_fastapi()
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
    conn = get_db_connection_fastapi()
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


# Serve static files
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Serve image assets
app.mount("/img", StaticFiles(directory="img"), name="images")

# Serve the shared JavaScript and CSS files
@app.get("/js/core/huapala-search.js")
async def get_huapala_search_js():
    """Serve the shared search component JavaScript"""
    try:
        with open("js/core/huapala-search.js", "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="huapala-search.js not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading JavaScript file: {str(e)}")

@app.get("/huapala-search.css")
async def get_huapala_search_css():
    """Serve the shared search component CSS"""
    try:
        with open("huapala-search.css", "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="text/css")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="huapala-search.css not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading CSS file: {str(e)}")

@app.get("/js/pages/app.js")
async def get_app_js():
    """Serve the main application JavaScript"""
    try:
        with open("js/pages/app.js", "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="app.js not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading JavaScript file: {str(e)}")

@app.get("/js/pages/song.js")
async def get_song_js():
    """Serve the song page JavaScript"""
    try:
        with open("js/pages/song.js", "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="song.js not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading JavaScript file: {str(e)}")

@app.get("/js/shared/settings.js")
async def get_settings_js():
    """Serve the settings JavaScript"""
    try:
        with open("js/shared/settings.js", "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="settings.js not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading JavaScript file: {str(e)}")

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request, error: Optional[str] = Query(None)):
    """Serve the admin login page"""
    return templates.TemplateResponse("admin/login.html", {
        "request": request,
        "error": error
    })

@app.post("/admin/login")
async def admin_login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...)
):
    """Handle admin login"""
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        # Create session
        token = create_session(username)
        
        # Set secure cookie
        response = RedirectResponse(url="/admin", status_code=302)
        response.set_cookie(
            key="admin_session",
            value=token,
            max_age=int(SESSION_TIMEOUT.total_seconds()),
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        return response
    else:
        # Redirect back to login with error
        return RedirectResponse(url="/admin/login?error=invalid", status_code=302)

@app.get("/admin/logout")
async def admin_logout(request: Request, response: Response):
    """Handle admin logout"""
    token = request.cookies.get("admin_session")
    if token and token in sessions:
        del sessions[token]
    
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("admin_session")
    return response

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Serve the admin dashboard with links to all admin functions"""
    # Check authentication
    auth_redirect = check_admin_auth(request)
    if auth_redirect:
        return auth_redirect
    
    # Get recently edited songs (top 3 most recently updated)
    db = SessionLocal()
    try:
        recent_songs = db.query(CanonicalMele)\
            .filter(CanonicalMele.updated_at.isnot(None))\
            .order_by(CanonicalMele.updated_at.desc())\
            .limit(3)\
            .all()
        
        recent_songs_data = []
        for song in recent_songs:
            recent_songs_data.append({
                'canonical_mele_id': song.canonical_mele_id,
                'canonical_title_hawaiian': song.canonical_title_hawaiian,
                'canonical_title_english': song.canonical_title_english,
                'primary_composer': song.primary_composer,
                'updated_at': song.updated_at
            })
    finally:
        db.close()
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "recent_songs": recent_songs_data,
        "show_logout": True
    })

@app.get("/admin/")
async def admin_dashboard_trailing_slash(request: Request):
    """Handle trailing slash for admin dashboard"""
    return await admin_dashboard(request)

@app.get("/admin/songs", response_class=HTMLResponse)
async def admin_songs_list(request: Request):
    """Serve admin songs list page"""
    # Check authentication
    auth_redirect = check_admin_auth(request)
    if auth_redirect:
        return auth_redirect
    
    # Get songs data from the existing songs endpoint
    db = SessionLocal()
    try:
        canonical_songs = db.query(CanonicalMele).order_by(CanonicalMele.canonical_title_hawaiian).all()
        songs_data = []
        for song in canonical_songs:
            songs_data.append({
                'canonical_mele_id': song.canonical_mele_id,
                'canonical_title_hawaiian': song.canonical_title_hawaiian,
                'canonical_title_english': song.canonical_title_english,
                'primary_composer': song.primary_composer
            })
    finally:
        db.close()
    
    return templates.TemplateResponse("admin/songs_list.html", {
        "request": request,
        "songs": songs_data,
        "show_logout": True
    })

# SQLAdmin login handlers removed

@app.get("/editor", response_class=HTMLResponse)
async def admin_interface_selector(request: Request):
    """Redirect to JSON editor (SQLAdmin removed)"""
    # Check authentication
    auth_redirect = check_admin_auth(request)
    if auth_redirect:
        return auth_redirect
    
    # Redirect directly to JSON editor since SQLAdmin is removed
    return RedirectResponse(url="/editor/legacy", status_code=302)

@app.get("/editor/legacy", response_class=HTMLResponse)
async def json_editor_page(request: Request):
    """Serve the JSON editor web interface (legacy backup)"""
    # Check authentication
    auth_redirect = check_admin_auth(request)
    if auth_redirect:
        return auth_redirect
    
    return templates.TemplateResponse("admin/editor.html", {
        "request": request,
        "show_logout": True
    })


# ==========================================
# COMPREHENSIVE SONG EDITOR ENDPOINTS
# ==========================================

def get_comprehensive_song_data(song_id: str) -> Dict[str, Any]:
    """Load complete song data from database using normalized tables"""
    db = SessionLocal()
    try:
        # Get canonical song data
        canonical_song = db.query(CanonicalMele).filter(CanonicalMele.canonical_mele_id == song_id).first()
        if not canonical_song:
            raise HTTPException(status_code=404, detail="Song not found")
        
        # Get related source data
        source_data = db.query(MeleSources).filter(MeleSources.canonical_mele_id == song_id).first()
        
        # Get related media data
        media_data = db.query(MeleMedia).filter(MeleMedia.canonical_mele_id == song_id).all()
        
        # Get verses from normalized tables
        verses_data = []
        if source_data:
            # Query verses with their lines
            verses = db.query(Verses).filter(
                Verses.mele_source_id == source_data.id
            ).order_by(Verses.verse_order).all()
            
            for verse in verses:
                # Get lines for this verse
                lines = db.query(VerseLines).filter(
                    VerseLines.verse_id == verse.id
                ).order_by(VerseLines.line_number).all()
                
                # Convert to the format expected by the editor
                verse_dict = {
                    "id": verse.verse_id,
                    "type": verse.verse_type,
                    "number": verse.verse_number,
                    "order": verse.verse_order,
                    "label": verse.label,
                    "lines": []
                }
                
                for line in lines:
                    line_dict = {
                        "id": line.line_id,
                        "line_number": line.line_number,
                        "hawaiian_text": line.hawaiian_text or "",
                        "english_text": line.english_text or "",
                        "is_bilingual": line.is_bilingual or False
                    }
                    verse_dict["lines"].append(line_dict)
                
                verses_data.append(verse_dict)
        
        return {
            "canonical_song": canonical_song,
            "source": source_data,
            "media": media_data,
            "verses": verses_data  # Add normalized verses data
        }
    finally:
        db.close()


def save_comprehensive_song_data(song_id: str, song_data: ComprehensiveSongModel) -> Dict[str, Any]:
    """Save complete song data to database with validation and backup"""
    print(f"DEBUG SAVE: Starting save_comprehensive_song_data for {song_id}")
    print(f"DEBUG SAVE: Song data has {len(song_data.lyrics.verses)} verses")
    db = SessionLocal()
    try:
        # Create backup before saving
        backup_filename = create_backup_filename(song_id, "before_comprehensive_edit")
        current_data = get_comprehensive_song_data(song_id)
        
        # Save backup to file
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir / backup_filename
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "song_id": song_id,
                "canonical_song": {
                    "canonical_mele_id": current_data["canonical_song"].canonical_mele_id,
                    "canonical_title_hawaiian": current_data["canonical_song"].canonical_title_hawaiian,
                    "canonical_title_english": current_data["canonical_song"].canonical_title_english,
                    "primary_composer": current_data["canonical_song"].primary_composer,
                    "primary_lyricist": current_data["canonical_song"].primary_lyricist,
                    "estimated_composition_date": current_data["canonical_song"].estimated_composition_date,
                    "cultural_significance_notes": current_data["canonical_song"].cultural_significance_notes,
                } if current_data["canonical_song"] else {},
                "source": {
                    "id": current_data["source"].id,
                    "composer": current_data["source"].composer,
                    "translator": current_data["source"].translator,
                    "hawaiian_editor": current_data["source"].hawaiian_editor,
                    "source_file": current_data["source"].source_file,
                    "source_publication": current_data["source"].source_publication,
                    "copyright_info": current_data["source"].copyright_info,
                    "verses_json": current_data["source"].verses_json,
                    "song_type": current_data["source"].song_type,
                    "structure_type": current_data["source"].structure_type,
                    "primary_location": current_data["source"].primary_location,
                    "island": current_data["source"].island,
                    "themes": current_data["source"].themes,
                    "mele_type": current_data["source"].mele_type,
                    "cultural_elements": current_data["source"].cultural_elements,
                } if current_data["source"] else {},
                "media": [
                    {
                        "id": media.id,
                        "url": media.url,
                        "media_type": media.media_type,
                        "title": media.title,
                        "description": media.description
                    } for media in current_data["media"]
                ] if current_data["media"] else []
            }
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        # Update canonical song data
        canonical_song = db.query(CanonicalMele).filter(CanonicalMele.canonical_mele_id == song_id).first()
        if canonical_song:
            canonical_song.canonical_title_hawaiian = song_data.canonical_title_hawaiian or None
            canonical_song.canonical_title_english = song_data.canonical_title_english or None
            canonical_song.primary_composer = song_data.primary_composer or None
            canonical_song.primary_lyricist = song_data.primary_lyricist or None
            canonical_song.estimated_composition_date = song_data.estimated_composition_date or None
            canonical_song.cultural_significance_notes = song_data.cultural_significance_notes or None
            canonical_song.updated_at = datetime.utcnow()
        
        # Update source data
        source = db.query(MeleSources).filter(MeleSources.canonical_mele_id == song_id).first()
        if source:
            source.composer = song_data.composer or None
            source.translator = song_data.translator or None
            source.hawaiian_editor = song_data.hawaiian_editor or None
            source.source_file = song_data.source_file or None
            source.source_publication = song_data.source_publication or None
            source.copyright_info = song_data.copyright_info or None
            source.song_type = song_data.song_type or None
            source.structure_type = song_data.structure_type or None
            source.primary_location = song_data.primary_location or None
            source.island = song_data.island.value if song_data.island else None
            source.themes = song_data.themes or None
            source.mele_type = song_data.mele_type or None
            source.cultural_elements = song_data.cultural_elements or None
            source.updated_at = datetime.utcnow()
            
            # Convert lyrics model back to JSON
            if song_data.lyrics and song_data.lyrics.verses:
                verses_json = {
                    "verses": [
                        {
                            "id": verse.id,
                            "type": verse.type,
                            "number": verse.number,
                            "order": verse.order,
                            "label": verse.label,
                            "lines": [
                                {
                                    "id": line.id,
                                    "line_number": line.line_number,
                                    "hawaiian_text": line.hawaiian_text,
                                    "english_text": line.english_text,
                                    "is_bilingual": line.is_bilingual
                                } for line in verse.lines
                            ]
                        } for verse in song_data.lyrics.verses
                    ],
                    "processing_metadata": song_data.lyrics.processing_metadata or {}
                }
                source.verses_json = verses_json
        
        # UPDATE NORMALIZED TABLES - This was missing!
        print(f"DEBUG SAVE: Updating normalized tables for {song_id}")
        
        # First, delete existing verses and lines for this song
        if source:
            # Delete existing verse lines first (due to foreign key constraints)
            existing_verses = db.query(Verses).filter(Verses.mele_source_id == source.id).all()
            for verse in existing_verses:
                db.query(VerseLines).filter(VerseLines.verse_id == verse.id).delete()
            
            # Delete existing verses
            db.query(Verses).filter(Verses.mele_source_id == source.id).delete()
            
            # Flush to ensure deletes complete before inserts
            db.flush()
            
            print(f"DEBUG SAVE: Deleted existing verses for source {source.id}")
            
            # Add new verses and lines from song_data
            if song_data.lyrics and song_data.lyrics.verses:
                for verse_data in song_data.lyrics.verses:
                    # Create new verse record
                    new_verse = Verses(
                        mele_source_id=source.id,
                        verse_id=verse_data.id,
                        verse_type=verse_data.type,
                        verse_number=verse_data.number,
                        verse_order=verse_data.order,
                        label=verse_data.label,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(new_verse)
                    db.flush()  # Get the ID
                    
                    print(f"DEBUG SAVE: Added verse {verse_data.id} with DB ID {new_verse.id}")
                    
                    # Create new line records
                    for line_data in verse_data.lines:
                        new_line = VerseLines(
                            verse_id=new_verse.id,
                            line_id=line_data.id,
                            line_number=line_data.line_number,
                            hawaiian_text=line_data.hawaiian_text,
                            english_text=line_data.english_text,
                            is_bilingual=line_data.is_bilingual,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        db.add(new_line)
                        print(f"DEBUG SAVE: Added line {line_data.line_number}: '{line_data.english_text[:30]}...'")
        
        # Handle media links
        if song_data.media_links:
            # Remove existing media
            db.query(MeleMedia).filter(MeleMedia.canonical_mele_id == song_id).delete()
            
            # Add new media links
            for media_link in song_data.media_links:
                if media_link.url:  # Only add if URL is provided
                    new_media = MeleMedia(
                        canonical_mele_id=song_id,
                        url=media_link.url,
                        media_type=media_link.media_type.value,
                        title=media_link.title,
                        description=media_link.description
                    )
                    db.add(new_media)
        
        # Commit all changes
        db.commit()
        
        return {
            "status": "success",
            "backup_created": str(backup_path),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving song data: {str(e)}")
    finally:
        db.close()


@app.get("/songs/{song_id}/edit-comprehensive", response_class=HTMLResponse)
async def comprehensive_song_editor(request: Request, song_id: str):
    """Serve the comprehensive song editor interface"""
    # Check authentication
    auth_redirect = check_admin_auth(request)
    if auth_redirect:
        return auth_redirect
    
    try:
        # Debug: Log the song_id being requested
        print(f"DEBUG COMPREHENSIVE EDITOR: Requested song_id = '{song_id}'")
        
        # Load song data
        song_data = get_comprehensive_song_data(song_id)
        
        # Debug: Log the loaded song data
        if song_data["canonical_song"]:
            print(f"DEBUG COMPREHENSIVE EDITOR: Loaded song title = '{song_data['canonical_song'].canonical_title_hawaiian}'")
        else:
            print(f"DEBUG COMPREHENSIVE EDITOR: No canonical song found for '{song_id}'")
        
        # Prepare song data for template
        canonical_dict = song_data["canonical_song"].__dict__ if song_data["canonical_song"] else {}
        
        # Use verses from normalized tables
        parsed_verses = None
        if song_data.get("verses"):
            # Verses are already loaded from normalized tables in the correct format
            parsed_verses = song_data["verses"]
            print(f"DEBUG: Loaded {len(parsed_verses)} verses from normalized tables for {song_id}")
            for i, verse in enumerate(parsed_verses):
                print(f"  Verse {i}: {verse.get('id', 'no-id')} - {verse.get('type', 'no-type')} - {len(verse.get('lines', []))} lines")
        
        # Debug: Log template context
        template_context = {
            **canonical_dict,
            "source": song_data["source"],
            "mele_media": song_data["media"],
            "parsed_verses": parsed_verses  # Add parsed verses to template context
        }
        print(f"DEBUG TEMPLATE CONTEXT: canonical_title_hawaiian = '{template_context.get('canonical_title_hawaiian', 'NOT_FOUND')}'")
        print(f"DEBUG TEMPLATE CONTEXT: canonical_mele_id = '{template_context.get('canonical_mele_id', 'NOT_FOUND')}'")
        
        return templates.TemplateResponse("comprehensive_song_editor.html", {
            "request": request,
            "song": template_context,
            "show_logout": True
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading song editor: {str(e)}")


@app.post("/songs/{song_id}/save")
async def save_comprehensive_song(request: Request, song_id: str):
    """Save comprehensive song data from form submission"""
    # Check authentication
    auth_redirect = check_admin_auth(request)
    if auth_redirect:
        return auth_redirect
    
    try:
        # Get form data
        form_data = await request.form()
        form_dict = dict(form_data)
        
        # Parse form data into song model
        song_data = FormProcessingModel.parse_form_data(form_dict)
        
        # Validate song data
        validation_result = validate_song_data(song_data)
        if not validation_result.is_valid:
            return templates.TemplateResponse("comprehensive_song_editor.html", {
                "request": request,
                "song": song_data.dict(),
                "status_message": f"Validation errors: {', '.join(validation_result.errors)}",
                "status_type": "error",
                "show_logout": True
            })
        
        # Save to database
        save_result = save_comprehensive_song_data(song_id, song_data)
        
        # Redirect back to editor with success message
        return RedirectResponse(
            url=f"/songs/{song_id}/edit-comprehensive?saved=true", 
            status_code=302
        )
        
    except Exception as e:
        # Load current song data for error display
        try:
            song_data = get_comprehensive_song_data(song_id)
            canonical_dict = song_data["canonical_song"].__dict__ if song_data["canonical_song"] else {}
            return templates.TemplateResponse("comprehensive_song_editor.html", {
                "request": request,
                "song": {
                    **canonical_dict,
                    "source": song_data["source"],
                    "mele_media": song_data["media"]
                },
                "status_message": f"Error saving song: {str(e)}",
                "status_type": "error",
                "show_logout": True
            })
        except:
            raise HTTPException(status_code=500, detail=f"Error saving song: {str(e)}")


@app.post("/songs/{song_id}/publish")
async def publish_comprehensive_song(request: Request, song_id: str):
    """Save and publish comprehensive song data"""
    # Check authentication
    auth_redirect = check_admin_auth(request)
    if auth_redirect:
        return auth_redirect
    
    try:
        # First save the song data (same as save endpoint)
        form_data = await request.form()
        form_dict = dict(form_data)
        print(f"DEBUG PUBLISH: Received {len(form_dict)} form fields for song {song_id}")
        print(f"DEBUG PUBLISH: Form keys: {list(form_dict.keys())[:10]}...")  # Show first 10 keys
        song_data = FormProcessingModel.parse_form_data(form_dict)
        
        validation_result = validate_song_data(song_data)
        if not validation_result.is_valid:
            raise HTTPException(status_code=400, detail=f"Validation errors: {', '.join(validation_result.errors)}")
        
        print(f"DEBUG PUBLISH: About to call save_comprehensive_song_data for {song_id}")
        save_result = save_comprehensive_song_data(song_id, song_data)
        print(f"DEBUG PUBLISH: save_comprehensive_song_data completed successfully")
        
        # TODO: Add publishing logic (e.g., regenerate static files, notify systems, etc.)
        
        return RedirectResponse(
            url=f"/songs/{song_id}/edit-comprehensive?published=true", 
            status_code=302
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error publishing song: {str(e)}")


@app.post("/songs/{song_id}/backup")
async def create_song_backup(request: Request, song_id: str, _auth: str = Depends(require_auth)):
    """Create manual backup of song data"""
    
    try:
        current_data = get_comprehensive_song_data(song_id)
        backup_filename = create_backup_filename(song_id, "manual")
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir / backup_filename
        
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "song_id": song_id,
            "action": "manual_backup",
            "data": current_data
        }
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)
        
        return {
            "status": "success",
            "backup_path": str(backup_path),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Error creating backup: {str(e)}"}, 500


# ==========================================
# END COMPREHENSIVE SONG EDITOR ENDPOINTS  
# ==========================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))