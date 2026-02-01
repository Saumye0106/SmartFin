# Microservices Design & Migration Plan

**Purpose:** Document the recommended microservice architecture for SmartFin and a pragmatic migration plan from the current monolith. This is a reference for engineering, deployment, and operations.

## 1. Objectives
- Break the monolith into small, independently deployable services.
- Enforce clear data ownership and API contracts.
- Improve scalability, fault isolation, and deployment velocity.
- Prepare infra for production-grade reliability (persistence, backups, monitoring).

## 2. High-level Service Map
- Auth Service
  - Responsibilities: register/login, password hashing, JWT issuance, refresh, user profile, password reset.
  - API surface: `POST /register`, `POST /login`, `POST /refresh`, `GET /me`.
  - Data: owns `users` table in Postgres (or separate DB).

- Inference Service
  - Responsibilities: load ML model(s) from object storage, expose `/predict` and `/whatif`, batch scoring endpoints.
  - API surface: `POST /predict`, `POST /whatif`, `GET /model-info`, `POST /batch-score` (async).
  - Data: reads model artifacts from S3; no direct write to user DB.

- Guidance / Business Logic Service
  - Responsibilities: spending pattern analysis, anomaly detection, investment suggestion rules, enrichment of raw predictions.
  - API surface: `POST /analyze` (accepts raw inputs or predicted score), `GET /recommendations`.
  - Data: may read aggregated user profile data; owns guidance rules and versioning.

- Frontend (Static)
  - Responsibilities: Single-page app assets; talk to API Gateway; host on CDN or GitHub Pages.

- API Gateway / Edge
  - Responsibilities: TLS termination, routing to services, JWT validation (optional), rate-limiting, caching, CORS, WAF rules.
  - Implementation options: managed gateway (Cloudflare, AWS API Gateway), Nginx/Traefik/Caddy for self-managed.

- Shared Infrastructure
  - Postgres (per-service schemas or separate DBs)
  - Redis (session store, cache, broker support via streams)
  - Object Storage (S3-compatible) for model artifacts and large files
  - Message broker (RabbitMQ, Redis Streams, or managed Pub/Sub) for async jobs
  - Monitoring & Logging stack (Prometheus + Grafana, ELK or hosted logging, Sentry)

## 3. Data Ownership & DB Strategy
- Own your data: each service should own its schema. Avoid cross-service direct DB reads/writes.
- Start with a single Postgres instance and use schemas per service; later split into managed databases if needed.
- Migrate `backend/auth.db` → `auth` schema in Postgres; run migrations with Alembic.
- Store sensitive tokens/secrets in environment or a secrets manager; never commit secrets.

## 4. API Contracts & Versioning
- Define OpenAPI specs for each service (store in `specs/` directory in repo).
- Use semantic versioning for APIs (v1/v2) and maintain backward compatibility; prefer separate endpoints for breaking changes.
- Use contract tests (Pact or OpenAPI-based) in CI to validate provider/consumer compatibility.

## 5. Communication Patterns
- Synchronous HTTP/REST for typical frontend → gateway → service calls.
- Async message broker for long-running tasks: batch scoring, model training, email notifications.
- Use idempotency keys for critical operations and retriable workflows.

## 6. Deployment & Orchestration
- Containerize each service with a `Dockerfile`.
- Local dev: `docker-compose.yaml` to start Postgres, Redis, Gateway, and services.
- Staging/Production: use managed containers (Render, ECS, GKE) or Kubernetes for larger scale.
- CI/CD: per-service pipelines to build, test, scan, push images, run migrations, and deploy.

Example minimal `docker-compose.yml` (starter):

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: smartfin
      POSTGRES_PASSWORD: smartfin
      POSTGRES_DB: smartfin
    volumes:
      - pgdata:/var/lib/postgresql/data
  redis:
    image: redis:7
  auth:
    build: ./services/auth
    environment:
      DATABASE_URL: postgres://smartfin:smartfin@postgres:5432/smartfin
    depends_on: [postgres]
  inference:
    build: ./services/inference
    environment:
      MODEL_BUCKET: local_models
    depends_on: [redis]
  gateway:
    image: traefik:v2.10
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
volumes:
  pgdata:
```

## 7. Migration Roadmap (incremental)
1. Define boundaries & OpenAPI specs for `auth`, `inference`, `guidance` services. (1-2 days)
2. Containerize current monolith and create `docker-compose` (1 day).
3. Extract Auth into `services/auth/` (3 days):
   - Move registration/login logic, switch to Postgres, add Alembic migrations, add Dockerfile and CI.
   - Update frontend `VITE_AUTH_BASE_URL` to point to auth service.
4. Extract Inference into `services/inference/` (3 days):
   - Load models from S3 (or local volume for staging), expose `/predict`.
   - Add async batch endpoints using message broker.
5. Introduce API Gateway and route traffic; test end-to-end in local Compose environment (2 days).
6. Migrate other business logic into `services/guidance/` as needed (3 days).
7. Harden infra: secrets manager, monitoring, backups, autoscaling (3-7 days).

Total initial effort (MVP microservices): 2-3 weeks for a single engineer to implement core services and CI pipelines.

## 8. Operations & Observability
- Add health/readiness probes for each service.
- Centralized logging (structured logs), tracing (OpenTelemetry), metrics (Prometheus/Grafana), error tracking (Sentry).
- Define SLOs and alerts (e.g., 95th percentile response < 500ms for `/predict`).

## 9. Security
- HTTPS everywhere; use managed TLS where possible.
- API Gateway enforces JWT validation, rate-limits, and CORS.
- Store secrets in a secret manager and rotate periodically.
- Use least-privilege IAM roles for object storage access.
- Conduct dependency scanning and periodic security audits.

## 10. Testing Strategy
- Unit tests for each service.
- Integration tests between services using test containers or a staging cluster.
- Contract tests for API compatibility.
- E2E tests (Playwright/Cypress) for critical user flows.

## 11. CI/CD Recommendations
- Per-service CI pipelines:
  - Run tests → Build image → Security scan → Publish image
  - Deployment step: run migrations (with locks) → deploy service → smoke tests
- Use feature branches and PR previews (deploy preview environments) before merging to `main`.

## 12. Runbooks & Backup
- Document runbooks for DB restore, model rollback, and scaling incidents.
- Schedule daily DB backups and store off-site (S3 or managed backups).

## 13. Checklist (short-term priorities)
- [ ] Define OpenAPI specs for `auth`, `inference`, `guidance`
- [ ] Add `Dockerfile` for each service
- [ ] Setup `docker-compose.yaml` for local orchestration
- [ ] Migrate `auth.db` → Postgres and add Alembic
- [ ] Add S3-compatible storage for model artifacts
- [ ] Add Redis for sessions and as message broker
- [ ] Create per-service CI pipelines
- [ ] Add monitoring and alerting

---

## References
- Microservices patterns: https://microservices.io/
- Twelve-Factor App: https://12factor.net/
- OpenAPI: https://swagger.io/specification/


*Document created: Feb 1, 2026.*
