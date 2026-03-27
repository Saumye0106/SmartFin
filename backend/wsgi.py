"""
WSGI entry point for SmartFin backend.
Used by Waitress (production) and can also be used by Gunicorn.
"""

import sys
import os

# Ensure the backend directory is on the path
sys.path.insert(0, os.path.dirname(__file__))

from app import app

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000, threads=4)
