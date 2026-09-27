"""
Chat domain helpers: session id scoping, title generation, and
persistence of conversation history to the chat_sessions table.
"""

import json
from datetime import datetime

from db_core import execute_query


def build_chat_session_title(text):
    """Generate a concise session title from the first user message."""
    if not text:
        return 'New Chat'
    normalized = ' '.join(text.strip().split())
    return (normalized[:57] + '...') if len(normalized) > 60 else normalized


def normalize_session_id(user_id, raw_session_id):
    """Ensure session IDs are user-scoped to avoid cross-user collisions."""
    base = (raw_session_id or '').strip()
    if not base:
        return f'user_{user_id}_default'
    user_prefix = f'user_{user_id}_'
    if base.startswith(user_prefix):
        return base
    return f'{user_prefix}{base}'


def load_chat_history(user_id, session_id):
    """Load a user's chat history from persistent storage."""
    row = execute_query(
        'SELECT conversation_json FROM chat_sessions WHERE session_id = ? AND user_id = ?',
        (session_id, user_id),
        fetch_one=True
    )
    if not row:
        return []

    raw = row.get('conversation_json') if isinstance(row, dict) else row['conversation_json']
    if not raw:
        return []
    try:
        history = json.loads(raw)
        return history if isinstance(history, list) else []
    except Exception:
        return []


def save_chat_history(user_id, session_id, user_message, updated_history):
    """Persist chat history, creating session row if missing."""
    now_iso = datetime.now().isoformat()
    existing = execute_query(
        'SELECT session_id, title FROM chat_sessions WHERE session_id = ? AND user_id = ?',
        (session_id, user_id),
        fetch_one=True
    )
    title = existing['title'] if existing and existing['title'] else build_chat_session_title(user_message)
    # Do not persist internal synthetic context-injection messages as user-visible chat.
    cleaned_history = []
    for msg in (updated_history or []):
        if not isinstance(msg, dict):
            continue
        role = msg.get('role')
        if role not in ('user', 'assistant'):
            continue

        content = msg.get('content')
        if isinstance(content, list):
            internal_context = False
            for block in content:
                if isinstance(block, dict) and isinstance(block.get('text'), str):
                    if block['text'].startswith('Trusted user data context (from internal services, use this for grounding):'):
                        internal_context = True
                        break
            if internal_context:
                continue

        cleaned_history.append(msg)

    conversation_json = json.dumps(cleaned_history)

    if existing:
        execute_query(
            '''
            UPDATE chat_sessions
            SET conversation_json = ?, updated_at = ?, last_message_at = ?, title = COALESCE(title, ?)
            WHERE session_id = ? AND user_id = ?
            ''',
            (conversation_json, now_iso, now_iso, title, session_id, user_id),
            commit=True
        )
    else:
        execute_query(
            '''
            INSERT INTO chat_sessions (session_id, user_id, title, conversation_json, created_at, updated_at, last_message_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (session_id, user_id, title, conversation_json, now_iso, now_iso, now_iso),
            commit=True
        )
