"""
Start a simple HTTP server serving `frontend/dist`, request the root page, print status and a snippet, then shut down.
"""
import os
import threading
import time
import sys

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

import requests

ROOT = os.path.join(os.path.dirname(__file__), '..')
DIST = os.path.join(ROOT, 'frontend', 'dist')
PORT = 5001

if not os.path.isdir(DIST):
    print('ERROR: dist directory not found:', DIST)
    sys.exit(2)

os.chdir(DIST)

server = ThreadingHTTPServer(('127.0.0.1', PORT), SimpleHTTPRequestHandler)

def start():
    server.serve_forever()

thread = threading.Thread(target=start, daemon=True)
thread.start()

# Wait for server
time.sleep(0.5)

try:
    r = requests.get(f'http://127.0.0.1:{PORT}', timeout=5)
    print('STATUS', r.status_code)
    snippet = r.text[:1000]
    print('\n---SNIPPET---\n')
    print(snippet)
    ok = 0 if r.status_code == 200 else 1
except Exception as e:
    print('ERROR during request:', str(e))
    ok = 3

server.shutdown()
thread.join()

sys.exit(ok)
