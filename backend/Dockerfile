# SmartFin backend.
#   docker build -t smartfin-backend backend                  # runtime image
#   docker build --target test -t smartfin-backend-test backend   # runs the test suite inside the image

FROM python:3.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# libgomp1: OpenMP runtime that xgboost and scikit-learn load at import time.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .


# ── Tests: the same code and libraries as the runtime image ──────────────────
FROM base AS test
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt
ENV SMARTFIN_LOG_FILE=
RUN python -m pytest -q \
    unit_test/test_statement_import.py unit_test/test_credit_report.py unit_test/test_risk_scorer.py \
    unit_test/test_budget_data_management.py unit_test/test_loan_schema.py unit_test/test_deployment.py \
    unit_test/test_postgres.py


# ── Runtime ──────────────────────────────────────────────────────────────────
FROM base AS runtime

# Run as an unprivileged user; /data is the only place the app writes.
RUN useradd --create-home --uid 10001 smartfin \
    && mkdir -p /data \
    && chown -R smartfin:smartfin /data /app \
    && rm -rf /app/unit_test
USER smartfin

ENV SMARTFIN_ENV=production \
    SMARTFIN_DATA_DIR=/data \
    SMARTFIN_LOG_FILE= \
    SMARTFIN_LOG_LEVEL=INFO

VOLUME ["/data"]
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5000/healthz', timeout=4).status == 200 else 1)"

# One process, several threads: SQLite allows a single writer, so the app runs as one replica.
CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "--threads=8", "wsgi:app"]
