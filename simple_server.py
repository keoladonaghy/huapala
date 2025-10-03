#!/usr/bin/env python3
"""
Simple HTTP server that serves both the main site and admin interface
"""

import http.server
import socketserver
import os
import json
from urllib.parse import urlparse

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Handle API routes
        if path == '/songs':
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
            # Send error response
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"error": f"Failed to load songs: {str(e)}"}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
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
                # Song not found
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = {"error": f"Song with ID '{song_id}' not found"}
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
                return
            
            # Send the song data
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(song, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            # Send error response
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"error": f"Failed to load song: {str(e)}"}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
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
            
            # Load the admin approval statuses
            # Note: In a real implementation, this would come from a database
            # For now, we'll simulate getting approved linkages from the admin interface
            approved_linkages = []
            
            # Filter linkages for this specific song that are approved
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
            # Send error response
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {"error": f"Failed to load songbooks: {str(e)}"}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

def run_server(port=8081):
    with socketserver.TCPServer(("", port), CustomHTTPRequestHandler) as httpd:
        print(f"Server running at http://localhost:{port}/")
        print(f"Main site: http://localhost:{port}/")
        print(f"Admin interface: http://localhost:{port}/admin/")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()