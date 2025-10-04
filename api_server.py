#!/usr/bin/env python3
"""
Enhanced HTTP server with database-driven API endpoints for the Huapala admin interface
"""

import http.server
import socketserver
import os
import json
import uuid
from urllib.parse import urlparse, parse_qs
from datetime import datetime, date
import io
import sys

# Database imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import get_database_url, People, Base

# Database setup
engine = create_engine(get_database_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def serialize_date(obj):
    """Helper function to serialize date objects to strings"""
    if isinstance(obj, date):
        return obj.isoformat()
    return obj

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Handle API routes
        if path == '/api/people':
            self.serve_people_api()
        elif path.startswith('/api/people/'):
            person_id = path[12:]  # Remove '/api/people/'
            self.serve_person_api(person_id)
        elif path == '/songs':
            self.serve_songs_api()
        elif path.startswith('/songs/'):
            # Handle different song endpoints
            path_parts = path[7:].split('/')  # Remove '/songs/' and split
            song_id = path_parts[0]
            
            if len(path_parts) == 2 and path_parts[1] == 'songbooks':
                # /songs/{song_id}/songbooks endpoint
                self.serve_song_songbooks_api(song_id)
            else:
                # /songs/{song_id} endpoint
                self.serve_song_api(song_id)
        # Handle admin routes
        elif path.startswith('/admin'):
            # Remove /admin prefix and serve from admin_build
            admin_path = path[6:]  # Remove '/admin'
            if admin_path == '' or admin_path == '/':
                admin_path = '/index.html'
            
            # Serve from admin_build directory
            self.path = admin_path
            original_directory = os.getcwd()
            try:
                os.chdir('admin_build')
                super().do_GET()
            finally:
                os.chdir(original_directory)
        else:
            # Serve main site files normally
            super().do_GET()
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/api/people':
            self.create_person_api()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_PUT(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path.startswith('/api/people/'):
            person_id = path[12:]  # Remove '/api/people/'
            self.update_person_api(person_id)
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_DELETE(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path.startswith('/api/people/'):
            person_id = path[12:]  # Remove '/api/people/'
            self.delete_person_api(person_id)
        else:
            self.send_response(404)
            self.end_headers()
    
    def serve_people_api(self):
        """Get all people from database"""
        try:
            db = SessionLocal()
            people = db.query(People).all()
            
            # Convert to dict format
            people_data = []
            for person in people:
                person_dict = {
                    "person_id": person.person_id,
                    "full_name": person.full_name,
                    "display_name": person.display_name,
                    "place_of_birth": person.place_of_birth,
                    "places_of_hawaiian_influence": person.places_of_hawaiian_influence or [],
                    "primary_influence_location": person.primary_influence_location,
                    "hawaiian_speaker": person.hawaiian_speaker,
                    "birth_date": serialize_date(person.birth_date),
                    "death_date": serialize_date(person.death_date),
                    "cultural_background": person.cultural_background,
                    "biographical_notes": person.biographical_notes or "",
                    "photograph": person.photograph,
                    "caption": person.caption,
                    "roles": person.roles or [],
                    "primary_role": person.primary_role or "",
                    "specialties": person.specialties or [],
                    "active_period_start": person.active_period_start,
                    "active_period_end": person.active_period_end,
                    "notable_works": person.notable_works or [],
                    "awards_honors": person.awards_honors or [],
                    "source_references": person.source_references or {"sources": [], "citations": []},
                    "verification_status": person.verification_status or "unverified",
                    "last_verified_date": serialize_date(person.last_verified_date)
                }
                people_data.append(person_dict)
            
            db.close()
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(people_data, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            # Add debug info about environment variables
            import os
            pgpass = os.getenv('PGPASSWORD')
            debug_info = f"PGPASSWORD set: {bool(pgpass)}"
            if pgpass:
                debug_info += f", length: {len(pgpass)}, starts: {pgpass[:3]}"
            self.send_error_response(500, f"Failed to load people: {str(e)} | Debug: {debug_info}")
    
    def serve_person_api(self, person_id):
        """Get individual person by ID"""
        try:
            db = SessionLocal()
            person = db.query(People).filter(People.person_id == person_id).first()
            
            if not person:
                db.close()
                self.send_error_response(404, f"Person with ID '{person_id}' not found")
                return
            
            person_dict = {
                "person_id": person.person_id,
                "full_name": person.full_name,
                "display_name": person.display_name,
                "place_of_birth": person.place_of_birth,
                "places_of_hawaiian_influence": person.places_of_hawaiian_influence or [],
                "primary_influence_location": person.primary_influence_location,
                "hawaiian_speaker": person.hawaiian_speaker,
                "birth_date": person.birth_date,
                "death_date": person.death_date,
                "cultural_background": person.cultural_background,
                "biographical_notes": person.biographical_notes or "",
                "photograph": person.photograph,
                "caption": person.caption,
                "roles": person.roles or [],
                "primary_role": person.primary_role or "",
                "specialties": person.specialties or [],
                "active_period_start": person.active_period_start,
                "active_period_end": person.active_period_end,
                "notable_works": person.notable_works or [],
                "awards_honors": person.awards_honors or [],
                "source_references": person.source_references or {"sources": [], "citations": []},
                "verification_status": person.verification_status or "unverified",
                "last_verified_date": person.last_verified_date
            }
            
            db.close()
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(person_dict, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_error_response(500, f"Failed to load person: {str(e)}")
    
    def create_person_api(self):
        """Create new person in database"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            person_data = json.loads(post_data.decode('utf-8'))
            
            # Generate unique ID if not provided
            if 'person_id' not in person_data or not person_data['person_id']:
                person_data['person_id'] = str(uuid.uuid4())
            
            db = SessionLocal()
            
            # Create new person
            new_person = People(
                person_id=person_data['person_id'],
                full_name=person_data.get('full_name'),
                display_name=person_data.get('display_name'),
                place_of_birth=person_data.get('place_of_birth'),
                places_of_hawaiian_influence=person_data.get('places_of_hawaiian_influence', []),
                primary_influence_location=person_data.get('primary_influence_location'),
                hawaiian_speaker=person_data.get('hawaiian_speaker'),
                birth_date=person_data.get('birth_date'),
                death_date=person_data.get('death_date'),
                cultural_background=person_data.get('cultural_background'),
                biographical_notes=person_data.get('biographical_notes', ''),
                photograph=person_data.get('photograph'),
                caption=person_data.get('caption'),
                roles=person_data.get('roles', []),
                primary_role=person_data.get('primary_role', ''),
                specialties=person_data.get('specialties', []),
                active_period_start=person_data.get('active_period_start'),
                active_period_end=person_data.get('active_period_end'),
                notable_works=person_data.get('notable_works', []),
                awards_honors=person_data.get('awards_honors', []),
                source_references=person_data.get('source_references', {"sources": [], "citations": []}),
                verification_status=person_data.get('verification_status', 'unverified'),
                last_verified_date=person_data.get('last_verified_date')
            )
            
            db.add(new_person)
            db.commit()
            
            # Return created person
            created_person = {
                "person_id": new_person.person_id,
                "full_name": new_person.full_name,
                "display_name": new_person.display_name,
                "place_of_birth": new_person.place_of_birth,
                "places_of_hawaiian_influence": new_person.places_of_hawaiian_influence or [],
                "primary_influence_location": new_person.primary_influence_location,
                "hawaiian_speaker": new_person.hawaiian_speaker,
                "birth_date": new_person.birth_date,
                "death_date": new_person.death_date,
                "cultural_background": new_person.cultural_background,
                "biographical_notes": new_person.biographical_notes or "",
                "photograph": new_person.photograph,
                "caption": new_person.caption,
                "roles": new_person.roles or [],
                "primary_role": new_person.primary_role or "",
                "specialties": new_person.specialties or [],
                "active_period_start": new_person.active_period_start,
                "active_period_end": new_person.active_period_end,
                "notable_works": new_person.notable_works or [],
                "awards_honors": new_person.awards_honors or [],
                "source_references": new_person.source_references or {"sources": [], "citations": []},
                "verification_status": new_person.verification_status or "unverified",
                "last_verified_date": new_person.last_verified_date
            }
            
            db.close()
            
            # Send response
            self.send_response(201)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(created_person, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_error_response(500, f"Failed to create person: {str(e)}")
    
    def update_person_api(self, person_id):
        """Update existing person in database"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            person_data = json.loads(post_data.decode('utf-8'))
            
            db = SessionLocal()
            person = db.query(People).filter(People.person_id == person_id).first()
            
            if not person:
                db.close()
                self.send_error_response(404, f"Person with ID '{person_id}' not found")
                return
            
            # Update person fields
            for field, value in person_data.items():
                if hasattr(person, field):
                    setattr(person, field, value)
            
            person.updated_at = datetime.utcnow()
            db.commit()
            
            # Return updated person
            updated_person = {
                "person_id": person.person_id,
                "full_name": person.full_name,
                "display_name": person.display_name,
                "place_of_birth": person.place_of_birth,
                "places_of_hawaiian_influence": person.places_of_hawaiian_influence or [],
                "primary_influence_location": person.primary_influence_location,
                "hawaiian_speaker": person.hawaiian_speaker,
                "birth_date": person.birth_date,
                "death_date": person.death_date,
                "cultural_background": person.cultural_background,
                "biographical_notes": person.biographical_notes or "",
                "photograph": person.photograph,
                "caption": person.caption,
                "roles": person.roles or [],
                "primary_role": person.primary_role or "",
                "specialties": person.specialties or [],
                "active_period_start": person.active_period_start,
                "active_period_end": person.active_period_end,
                "notable_works": person.notable_works or [],
                "awards_honors": person.awards_honors or [],
                "source_references": person.source_references or {"sources": [], "citations": []},
                "verification_status": person.verification_status or "unverified",
                "last_verified_date": person.last_verified_date
            }
            
            db.close()
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(updated_person, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_error_response(500, f"Failed to update person: {str(e)}")
    
    def delete_person_api(self, person_id):
        """Delete person from database"""
        try:
            db = SessionLocal()
            person = db.query(People).filter(People.person_id == person_id).first()
            
            if not person:
                db.close()
                self.send_error_response(404, f"Person with ID '{person_id}' not found")
                return
            
            db.delete(person)
            db.commit()
            db.close()
            
            # Send response
            self.send_response(204)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
        except Exception as e:
            self.send_error_response(500, f"Failed to delete person: {str(e)}")
    
    def send_error_response(self, status_code, message):
        """Send JSON error response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        error_response = {"error": message}
        self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    # Original song API methods from simple_server.py
    def serve_songs_api(self):
        """Serve songs data from JSON file"""
        try:
            with open('docs/songs-data.json', 'r', encoding='utf-8') as f:
                songs_data = json.load(f)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(songs_data, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_error_response(500, f"Failed to load songs: {str(e)}")
    
    def serve_song_api(self, song_id):
        """Serve individual song data by ID"""
        try:
            with open('docs/songs-data.json', 'r', encoding='utf-8') as f:
                songs_data = json.load(f)
            
            # Find the song with matching canonical_mele_id
            song = None
            for s in songs_data:
                if s.get('canonical_mele_id') == song_id:
                    song = s
                    break
            
            if not song:
                self.send_error_response(404, f"Song with ID '{song_id}' not found")
                return
            
            # Send the song data
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(song, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_error_response(500, f"Failed to load song: {str(e)}")
    
    def serve_song_songbooks_api(self, song_id):
        """Serve approved songbook entries for a specific song"""
        try:
            # Load the suggested linkages (which includes approved ones)
            linkages_data = []
            try:
                with open('data/songbooks/suggested_linkages.json', 'r', encoding='utf-8') as f:
                    linkages_data = json.load(f)
            except FileNotFoundError:
                # If no linkages file exists yet, return empty array
                pass
            
            # Filter linkages for this specific song that are approved
            approved_linkages = []
            for linkage in linkages_data:
                if linkage.get('canonical_mele_id') == song_id and linkage.get('match_status') == 'approved':
                    songbook_entry = {
                        'songbook_name': linkage.get('songbook_name'),
                        'songbook_entry_title': linkage.get('songbook_entry_title'),
                        'page': linkage.get('page'),
                        'pub_year': linkage.get('pub_year'),
                        'composer': linkage.get('composer'),
                        'similarity_score': linkage.get('similarity_score')
                    }
                    approved_linkages.append(songbook_entry)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = {
                'song_id': song_id,
                'songbooks': approved_linkages,
                'count': len(approved_linkages)
            }
            
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_error_response(500, f"Failed to load songbooks: {str(e)}")

def run_server(port=8081):
    with socketserver.TCPServer(("", port), CustomHTTPRequestHandler) as httpd:
        print(f"API server running at http://localhost:{port}/")
        print(f"Main site: http://localhost:{port}/")
        print(f"Admin interface: http://localhost:{port}/admin/")
        print(f"People API: http://localhost:{port}/api/people")
        httpd.serve_forever()

if __name__ == "__main__":
    # Use Railway's PORT environment variable if available
    port = int(os.getenv('PORT', 8081))
    print(f"Starting server with database host: {os.getenv('PGHOST', 'not set')}")
    run_server(port)