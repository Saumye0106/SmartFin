"""Deployment wiring: every backend route must be reachable through the frontend's nginx, and config comes from the environment."""

import importlib
import re
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

# In the image the frontend folder isn't present; the routing test then has nothing to check against.
NGINX_CONF = BACKEND.parent / "frontend" / "nginx.conf.template"
SPA_PAGES = {"/forgot-password", "/verify-email"}   # also React pages: nginx sends only non-GET requests to the backend


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    import os
    os.environ.setdefault("SMARTFIN_LOG_FILE", "")
    return importlib.import_module("app").app


@pytest.mark.skipif(not NGINX_CONF.exists(), reason="frontend/nginx.conf.template not available (running inside the backend image)")
def test_every_backend_route_is_forwarded_by_nginx(app):
    conf = NGINX_CONF.read_text(encoding="utf-8")
    prefixes = re.findall(r"location (/[\w\-/]+/) \{\s*proxy_pass", conf)
    exact = re.search(r"location ~ \^/\(([^)]+)\)\$ \{\s*proxy_pass", conf).group(1).split("|")
    by_method = re.search(r"location ~ \^/\(([^)]+)\)\$ \{\s*error_page 418 = @backend", conf).group(1).split("|")
    assert set("/" + p for p in by_method) == SPA_PAGES

    unrouted = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static" or rule.rule == "/":
            continue   # "/" is the React app; the backend's own "/" status page is replaced by /healthz
        path = rule.rule
        covered = any(path.startswith(p) for p in prefixes) or path.lstrip("/") in exact or path in SPA_PAGES
        if not covered:
            unrouted.append(path)
    assert unrouted == [], f"add these backend routes to frontend/nginx.conf.template: {unrouted}"
    # the exact-match list must not shadow a React page
    assert not {"auth", "dashboard", "profile", "goals", "loans", "budget", "chat", "portfolio", "nudges", "retirement"} & set(exact)


def test_healthz(app):
    r = app.test_client().get("/healthz")
    assert r.status_code == 200 and r.get_json() == {"status": "ok"}


def test_data_dir_and_secret_come_from_the_environment(tmp_path):
    """Run in a subprocess: these are read once, at import."""
    import os
    import subprocess

    env = {**os.environ, "SMARTFIN_DATA_DIR": str(tmp_path / "data"), "SMARTFIN_LOG_FILE": "", "PYTHONUTF8": "1"}
    code = ("import db_core, app; print(db_core.DB_PATH); print(app.app.config['UPLOAD_FOLDER']); "
            "print(app.app.test_client().get('/healthz').status_code)")
    out = subprocess.run([sys.executable, "-c", code], cwd=BACKEND, env=env, capture_output=True, text=True, timeout=180)
    lines = [ln for ln in out.stdout.splitlines() if ln.strip()][-3:]
    assert out.returncode == 0, out.stderr[-600:]
    assert Path(lines[0]) == tmp_path / "data" / "auth.db" and (tmp_path / "data" / "auth.db").exists()
    assert Path(lines[1]) == tmp_path / "data" / "uploads" / "profile_pictures" and lines[2] == "200"

    # production refuses the built-in development secret (tested with dotenv disabled so a local .env can't supply one)
    code = "import dotenv; dotenv.load_dotenv = lambda *a, **k: False\nimport app"
    for secret, ok in (("smartfin-secret-key-change-in-production", False), ("short", False), ("x" * 40, True)):
        bad = subprocess.run([sys.executable, "-c", code], cwd=BACKEND, capture_output=True, text=True, timeout=180,
                             env={**env, "SMARTFIN_ENV": "production", "JWT_SECRET_KEY": secret})
        assert (bad.returncode == 0) == ok, (secret, bad.stderr[-300:])
        if not ok:
            assert "JWT_SECRET_KEY" in bad.stderr
