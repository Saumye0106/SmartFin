"""
Simple HTTP server for SmartFin frontend
Run this to serve the frontend properly
"""
import http.server
import socketserver
import os

PORT = 8000

# Change to frontend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

Handler = http.server.SimpleHTTPRequestHandler

print("=" * 60)
print("SmartFin Frontend Server")
print("=" * 60)
print(f"\nStarting server on port {PORT}...")
print(f"\nOpen in browser: http://localhost:{PORT}")
print(f"\nMake sure backend is running on port 5000!")
print("\nPress Ctrl+C to stop")
print("=" * 60 + "\n")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
