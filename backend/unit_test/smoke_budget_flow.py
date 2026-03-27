import json
import time
from urllib import request

BASE = "http://127.0.0.1:5000"
EMAIL = f"smoke{int(time.time())}@example.com"
PASSWORD = "Pass123!"


def post(path, payload, token=None):
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(BASE + path, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def put(path, payload, token=None):
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(BASE + path, data=data, method="PUT")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get(path, token=None):
    req = request.Request(BASE + path, method="GET")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


# Register (ignore if account already exists)
try:
    post("/register", {"email": EMAIL, "password": PASSWORD})
except Exception:
    pass

login = post("/login", {"email": EMAIL, "password": PASSWORD})
token = login.get("token")
if not token:
    raise RuntimeError("No token returned from /login")

month = time.strftime("%Y-%m")
today = time.strftime("%Y-%m-%d")

budget = post(
    "/api/budget/monthly",
    {
        "month": month,
        "monthly_income": 90000,
        "planned_savings": 25000,
        "category_budgets": {
            "rent": 25000,
            "food": 12000,
            "travel": 5000,
            "shopping": 4000,
            "emi": 8000,
            "utilities": 3500,
            "other": 3000,
        },
    },
    token,
)

expense = post(
    "/api/budget/expenses",
    {
        "expense_date": today,
        "category": "food",
        "amount": 2200,
        "note": "smoke-expense",
    },
    token,
)
expense_id = expense["expense"]["id"]

updated = put(
    f"/api/budget/expenses/{expense_id}",
    {"amount": 2600, "note": "smoke-expense-updated"},
    token,
)

summary = get(f"/api/budget/summary?month={month}", token)
predict = post("/api/predict/from-budget", {"month": month}, token)
chat = post(
    "/api/chat",
    {"message": "Show my budget and expense summary for this month"},
    token,
)

result = {
    "email": EMAIL,
    "budget_saved": bool(budget.get("success")),
    "expense_created": bool(expense.get("success")),
    "expense_updated": bool(updated.get("success")),
    "summary_count": summary.get("summary", {}).get("expense_count"),
    "predict_score": predict.get("score"),
    "chat_success": bool(chat.get("success")),
    "chat_has_response": bool((chat.get("response") or "").strip()),
}

print(json.dumps(result, indent=2))
