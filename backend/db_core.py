"""
Shared SQLite helpers for the Flask app and its blueprints.
Uses Flask's `g` to keep one connection per request context.
"""

import os
import sqlite3
import dbapi

from flask import g

# Everything SmartFin writes (the database and uploaded pictures) lives under DATA_DIR.
# Locally that is this folder; in a container it is a mounted volume (SMARTFIN_DATA_DIR=/data),
# so the data survives the container being replaced.
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.environ.get('SMARTFIN_DATA_DIR') or BACKEND_DIR)
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, 'auth.db')
UPLOAD_DIR = os.path.join(DATA_DIR, 'uploads', 'profile_pictures')


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = dbapi.connect(DB_PATH)   # SQLite file, or PostgreSQL when DATABASE_URL is set
        db.row_factory = sqlite3.Row
    return db


def close_connection(exception=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def execute_query(query, params=(), fetch_one=False, fetch_all=False, commit=False):
    """
    Execute a database query with proper error handling

    Args:
        query: SQL query string
        params: Query parameters tuple
        fetch_one: Return single row
        fetch_all: Return all rows
        commit: Commit transaction

    Returns:
        Query result or None
    """
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute(query, params)
        if commit:
            db.commit()
            return cur.lastrowid
        if fetch_one:
            return cur.fetchone()
        if fetch_all:
            return cur.fetchall()
        return None
    except sqlite3.Error as e:
        if commit:
            db.rollback()
        raise e


def row_to_dict(row):
    """Convert sqlite3.Row to dictionary"""
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows):
    """Convert list of sqlite3.Row to list of dictionaries"""
    return [dict(row) for row in rows]
