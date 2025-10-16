#!/usr/bin/env python3
"""
Simple HTTP server to view static HTML files
Works on any Python version including 3.14
"""
import http.server
import socketserver
from pathlib import Path
import os

PORT = 8000
DIRECTORY = "web_static"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

if __name__ == "__main__":
    os.chdir(Path(__file__).parent)

    with socketserver.TCPServer(("127.0.0.1", PORT), MyHTTPRequestHandler) as httpd:
        print("=" * 80)
        print("  Simple Static File Server")
        print("=" * 80)
        print(f"  Serving files from: {DIRECTORY}/")
        print(f"  Server running at: http://localhost:{PORT}")
        print()
        print("  View the HTML files:")
        print(f"    Main Dashboard: http://localhost:{PORT}/index.html")
        print(f"    Applications:   http://localhost:{PORT}/applications.html")
        print(f"    DNS Validation: http://localhost:{PORT}/dns.html")
        print()
        print("  NOTE: API endpoints won't work (static files only)")
        print("  Press CTRL+C to stop")
        print("=" * 80)
        httpd.serve_forever()
