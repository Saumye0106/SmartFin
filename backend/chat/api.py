"""
Chat Blueprint
AI chat agent endpoint plus session management (list/history/rename/delete/clear).
"""

from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from db_core import get_db, execute_query, rows_to_list
from chat.service import (
    normalize_session_id,
    load_chat_history,
    save_chat_history,
)

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/api/chat', methods=['POST'])
@jwt_required()
def chat_endpoint():
    """
    Chat with the SmartFin AI agent.
    Body: { message: str, session_id?: str }
    Auth: Bearer JWT token required
    """
    try:
        user_id = int(get_jwt_identity())
        db = get_db()
        user = db.execute('SELECT id, username FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 401

        user_email = user['username']

        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = normalize_session_id(user_id, data.get('session_id', f'user_{user_id}_default'))

        if not user_message:
            return jsonify({'error': 'Message is required'}), 400

        # Load persisted conversation history
        conversation_history = load_chat_history(user_id, session_id)

        # Build app context for tool execution
        app_context = {
            'user_id': user_id,
            'user_email': user_email,
        }

        # Call the chat agent
        from chat_agent import chat as agent_chat
        assistant_text, updated_history, widgets = agent_chat(
            user_message, conversation_history, app_context
        )

        # Persist updated history
        save_chat_history(user_id, session_id, user_message, updated_history)

        return jsonify({
            'success': True,
            'response': assistant_text,
            'widgets': widgets,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Chat agent error: {str(e)}'
        }), 500


@chat_bp.route('/api/chat/clear', methods=['POST'])
@jwt_required()
def clear_chat():
    """Clear chat history for a session."""
    try:
        user_id = int(get_jwt_identity())

        data = request.get_json() or {}
        session_id = normalize_session_id(user_id, data.get('session_id', f'user_{user_id}_default'))

        execute_query(
            'DELETE FROM chat_sessions WHERE session_id = ? AND user_id = ?',
            (session_id, user_id),
            commit=True
        )

        return jsonify({'success': True, 'message': 'Chat history cleared'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/api/chat/sessions', methods=['GET'])
@jwt_required()
def list_chat_sessions():
    """List saved chat sessions for the authenticated user."""
    try:
        user_id = int(get_jwt_identity())
        sessions = execute_query(
            '''
            SELECT session_id, title, created_at, updated_at, last_message_at
            FROM chat_sessions
            WHERE user_id = ?
            ORDER BY last_message_at DESC
            ''',
            (user_id,),
            fetch_all=True
        )
        return jsonify({
            'success': True,
            'sessions': rows_to_list(sessions),
            'count': len(sessions)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/api/chat/history', methods=['GET'])
@jwt_required()
def get_chat_history():
    """Get a full saved chat history for a session."""
    try:
        user_id = int(get_jwt_identity())
        session_id = normalize_session_id(user_id, request.args.get('session_id', f'user_{user_id}_default'))
        history = load_chat_history(user_id, session_id)
        return jsonify({
            'success': True,
            'session_id': session_id,
            'history': history,
            'message_count': len(history)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/api/chat/session/title', methods=['PUT'])
@jwt_required()
def rename_chat_session():
    """Rename a saved chat session title."""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        session_id = normalize_session_id(user_id, data.get('session_id'))
        title = (data.get('title') or '').strip()

        if not title:
            return jsonify({'error': 'title is required'}), 400

        existing = execute_query(
            'SELECT session_id FROM chat_sessions WHERE session_id = ? AND user_id = ?',
            (session_id, user_id),
            fetch_one=True
        )
        if not existing:
            return jsonify({'error': 'session not found'}), 404

        execute_query(
            '''
            UPDATE chat_sessions
            SET title = ?, updated_at = ?
            WHERE session_id = ? AND user_id = ?
            ''',
            (title[:120], datetime.now().isoformat(), session_id, user_id),
            commit=True
        )

        return jsonify({'success': True, 'session_id': session_id, 'title': title[:120]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/api/chat/session', methods=['DELETE'])
@jwt_required()
def delete_chat_session():
    """Delete a specific saved chat session."""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        session_id = normalize_session_id(user_id, data.get('session_id'))

        execute_query(
            'DELETE FROM chat_sessions WHERE session_id = ? AND user_id = ?',
            (session_id, user_id),
            commit=True
        )

        return jsonify({'success': True, 'message': 'Chat session deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
