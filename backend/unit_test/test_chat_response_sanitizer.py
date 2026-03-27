import os
import sys


# Ensure backend package is importable when running from repo root.
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from chat_agent import _sanitize_assistant_text


def test_sanitize_removes_meta_reasoning_prefix_line():
    leaked = "The user wants me to explain budgeting.\nHere is a simple 50/30/20 plan."

    cleaned = _sanitize_assistant_text(leaked)

    assert cleaned == "Here is a simple 50/30/20 plan."


def test_sanitize_uses_final_answer_section_when_present():
    leaked = "Thinking...\nI should call tools.\nFinal Answer: Your savings rate is 28%, which is healthy."

    cleaned = _sanitize_assistant_text(leaked)

    assert cleaned == "Your savings rate is 28%, which is healthy."


def test_sanitize_preserves_normal_user_facing_response():
    normal = "Your EMI-to-income ratio is 22%, which is within a safe range."

    cleaned = _sanitize_assistant_text(normal)

    assert cleaned == normal


def test_sanitize_fallback_when_only_meta_lines_exist():
    leaked_only = "Let me think about this.\nI should analyze your profile first."

    cleaned = _sanitize_assistant_text(leaked_only)

    assert cleaned == "I can help with that. Could you share a bit more detail?"
