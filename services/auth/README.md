# Auth Service (minimal scaffold)

This is a minimal authentication service used for Sprint 1 scaffolding.

Endpoints:
- `POST /register`  -- JSON body: `{ "email": "...", "password": "..." }`
- `POST /login`     -- JSON body: `{ "email": "...", "password": "..." }`
- `GET /protected`  -- requires `Authorization: Bearer <token>` header

Local quickstart:

```bash
# create a venv and install
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt

# initialize DB (the app will create DB on first run as well)
python app.py

# run tests
pytest -q
```

Configuration:
- `AUTH_DB` environment variable to set DB path (defaults to `services/auth/auth.db`)
- `AUTH_JWT_SECRET` to set JWT secret (defaults to `dev-secret`)

Security recommendations (MVP):
- Use a strong `AUTH_JWT_SECRET` in production (recommended 32+ random bytes).
- Default access token expiry is 30 minutes. For MVP this balances usability and security.
- For production consider using refresh tokens and secure httpOnly cookies for storage.
