import json
import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import app as smartfin_app


def post_json(client, path, payload, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.post(path, data=json.dumps(payload), headers=headers)


def put_json(client, path, payload, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.put(path, data=json.dumps(payload), headers=headers)


def get_json(client, path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.get(path, headers=headers)


def main():
    app = smartfin_app.app
    app.config["TESTING"] = True
    client = app.test_client()

    email = f"smoke_testclient_{int(time.time())}@example.com"
    password = "Pass123!"

    register_resp = post_json(client, "/register", {"email": email, "password": password})
    if register_resp.status_code not in (200, 201, 409):
        raise RuntimeError(f"register failed: {register_resp.status_code} {register_resp.data.decode('utf-8', errors='ignore')}")

    login_resp = post_json(client, "/login", {"email": email, "password": password})
    if login_resp.status_code != 200:
        raise RuntimeError(f"login failed: {login_resp.status_code} {login_resp.data.decode('utf-8', errors='ignore')}")

    login_data = login_resp.get_json() or {}
    token = login_data.get("token")
    if not token:
        raise RuntimeError("No token returned from /login")

    month = time.strftime("%Y-%m")
    today = time.strftime("%Y-%m-%d")

    budget_resp = post_json(
        client,
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
    if budget_resp.status_code != 200:
        raise RuntimeError(f"budget upsert failed: {budget_resp.status_code} {budget_resp.data.decode('utf-8', errors='ignore')}")

    expense_resp = post_json(
        client,
        "/api/budget/expenses",
        {
            "expense_date": today,
            "category": "food",
            "amount": 2200,
            "note": "smoke-expense",
        },
        token,
    )
    if expense_resp.status_code != 201:
        raise RuntimeError(f"expense create failed: {expense_resp.status_code} {expense_resp.data.decode('utf-8', errors='ignore')}")

    expense_data = expense_resp.get_json() or {}
    expense_id = ((expense_data.get("expense") or {}).get("id"))
    if not expense_id:
        raise RuntimeError("No expense id in create response")

    expense_update_resp = put_json(
        client,
        f"/api/budget/expenses/{expense_id}",
        {"amount": 2600, "note": "smoke-expense-updated"},
        token,
    )
    if expense_update_resp.status_code != 200:
        raise RuntimeError(f"expense update failed: {expense_update_resp.status_code} {expense_update_resp.data.decode('utf-8', errors='ignore')}")

    summary_resp = get_json(client, f"/api/budget/summary?month={month}", token)
    if summary_resp.status_code != 200:
        raise RuntimeError(f"summary failed: {summary_resp.status_code} {summary_resp.data.decode('utf-8', errors='ignore')}")

    predict_resp = post_json(client, "/api/predict/from-budget", {"month": month}, token)
    if predict_resp.status_code != 200:
        raise RuntimeError(f"predict from budget failed: {predict_resp.status_code} {predict_resp.data.decode('utf-8', errors='ignore')}")

    chat_resp = post_json(client, "/api/chat", {"message": "Show my budget and expense summary for this month"}, token)
    if chat_resp.status_code != 200:
        raise RuntimeError(f"chat failed: {chat_resp.status_code} {chat_resp.data.decode('utf-8', errors='ignore')}")

    summary_data = summary_resp.get_json() or {}
    predict_data = predict_resp.get_json() or {}
    chat_data = chat_resp.get_json() or {}

    result = {
        "budget_saved": bool((budget_resp.get_json() or {}).get("success")),
        "expense_created": bool((expense_resp.get_json() or {}).get("success")),
        "expense_updated": bool((expense_update_resp.get_json() or {}).get("success")),
        "summary_count": ((summary_data.get("summary") or {}).get("expense_count")),
        "predict_score": predict_data.get("score"),
        "chat_success": bool(chat_data.get("success")),
        "chat_has_response": bool((chat_data.get("response") or "").strip()),
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
