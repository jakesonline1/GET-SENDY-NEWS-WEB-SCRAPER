# Get Sendy News Web Scraper - Phase 1

Phase 1 implementation of a future fully automated news-to-social pipeline.

## Stack
- Backend: FastAPI + Postgres + Celery + Redis
- Frontend: Next.js (TypeScript)
- Storage: local filesystem dev + MinIO (S3-compatible)
- Auth: email/password with hashed passwords and role-based access (admin/reviewer)

## Pipeline Core
Canonical object: `content_packs`

Statuses:
`NEW → ENRICHED → DRAFT_READY → IN_REVIEW → APPROVED → ARCHIVED`

Future statuses modeled:
`ASSETS_PENDING`, `SCHEDULED`, `POSTED`

## Plugins
Interfaces:
- Ingestor
- Enricher (dedupe/tag/geocode/weather)
- Generator (caption draft, cover spec, carousel outline)

Default v1 generator outputs:
- 5 headline options
- 1 cover-page text spec
- 1 short + 1 long caption
- 1 carousel outline (5 slides)

Stored in `creative_drafts` linked to `content_packs`.

## Start
```bash
docker compose up --build
```

Login:
- `admin@getsendy.dev` / `password123`
- `reviewer@getsendy.dev` / `password123`

Web UI: http://localhost:3000
API docs: http://localhost:8000/docs
MinIO console: http://localhost:9001

## Tests
```bash
cd backend
pip install -r requirements.txt
PYTHONPATH=. pytest
```

## Troubleshooting
- Password hashing now uses `pbkdf2_sha256` to avoid bcrypt runtime incompatibilities in Docker. If login still fails after dependency changes, rebuild API/worker images:
  ```bash
  docker compose down -v
  docker compose build --no-cache api worker
  docker compose up
  ```
- If API crashes at startup with email validation errors, ensure dependencies are installed from `backend/requirements.txt` (includes `email-validator`).
- API now seeds users during FastAPI startup after DB readiness checks, instead of running a separate pre-uvicorn seed command.

- If `http://localhost:8000/docs` is unreachable after `docker compose up`, run:
  ```bash
  docker compose ps
  docker compose logs api --tail=200
  ```
  The stack now waits for Postgres health before API/worker startup and retries DB connection during seed.
- If login fails, verify the seeded users exist by recreating from scratch:
  ```bash
  docker compose down -v
  docker compose up --build
  ```
  Then sign in with `admin@getsendy.dev` / `password123`.
