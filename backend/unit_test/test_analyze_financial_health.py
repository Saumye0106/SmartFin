import requests

BASE = "http://localhost:5000"
EMAIL = "bedrock-test@smartfin.local"
PASSWORD = "TestPassword123!"

login = requests.post(
    f"{BASE}/login",
    json={"email": EMAIL, "password": PASSWORD},
    timeout=10,
)
login.raise_for_status()
token = login.json()["token"]

resp = requests.post(
    f"{BASE}/api/chat",
    json={"message": "analyze my financial health", "conversation_id": "tool-error-repro-1"},
    headers={"Authorization": f"Bearer {token}"},
    timeout=45,
)
print(resp.status_code)
print(resp.text)
