import json
import sqlite3
from pathlib import Path

import requests

BASE = "http://localhost:5000"
EMAIL = "bedrock-test@smartfin.local"
PASSWORD = "TestPassword123!"
DB_PATH = Path(__file__).parent / "backend" / "auth.db"


def ensure_profile_exists(user_id: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO users_profile
            (user_id, name, age, location, risk_tolerance, notification_preferences, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (
                user_id,
                "Bedrock Test User",
                29,
                "Chennai",
                4,
                '{"email": true, "push": false, "in_app": true, "frequency": "daily"}',
            ),
        )
        conn.commit()
    finally:
        conn.close()


login = requests.post(
    f"{BASE}/login",
    json={"email": EMAIL, "password": PASSWORD},
    timeout=10,
)
login.raise_for_status()
login_data = login.json()
token = login_data["token"]
user_id = int(login_data["user"]["id"])

ensure_profile_exists(user_id)

resp = requests.post(
    f"{BASE}/api/chat",
    json={"message": "analyze my financial health", "conversation_id": "multi-tool-check"},
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    timeout=60,
)

print(resp.status_code)
print(resp.text)

# Optional second turn with same conversation to ensure no dangling tool ids
resp2 = requests.post(
    f"{BASE}/api/chat",
    json={"message": "continue", "conversation_id": "multi-tool-check"},
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    timeout=60,
)
print(resp2.status_code)
print(resp2.text)
