# AGENTS.md — Tracking Success

Conventions for AI assistants working in this repository.

## Response Protocol

- Be concise and direct
- When uncertain, ask — do not assume

## Project Identity

- **Owner:** Jonas Krauss (jkrauss)
- **Purpose:** Personal metrics tracker — daily tracking of sleep, fasting, mood, weight, habits
- **Stack:** FastAPI + SQLAlchemy + PostgreSQL (backend), React + Vite + TypeScript + Tailwind + shadcn/ui (frontend)
- **Infrastructure:** Docker Compose, Traefik v3, Let's Encrypt, Hetzner Cloud
- **Email:** Sweego API (transactional emails via `support.jonaskrauss.de`)
- **Guiding principle:** Ponytail — simplest solution that works, stdlib first, fewest files

## Architecture

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  React   │────▶│  nginx   │────▶│ Traefik  │──▶ Internet
│ (Vite)   │     │ (SPA)    │     │ (TLS)    │
└──────────┘     └────┬─────┘     └──────────┘
                      │ /api/
                      ▼
                ┌──────────┐     ┌──────────┐
                │ FastAPI  │────▶│ Postgres │
                │ (uvicorn)│     │ (asyncpg)│
                └──────────┘     └──────────┘
```

- **Backend:** `backend/` — FastAPI app with async SQLAlchemy, JWT auth, Sweego email
- **Frontend:** `frontend/` — React SPA served by nginx, proxies `/api/` to backend
- **Database:** PostgreSQL 16 (Alpine), async via asyncpg + SQLAlchemy
- **Auth:** JWT tokens, email confirmation on registration, password reset via email tokens

## Code Style

### Backend (Python)

- **Line length:** 100 (ruff)
- **Async everywhere:** all DB operations use `async/await`
- **No new dependencies** without explicit approval — prefer stdlib (`urllib.request`, `hashlib`, `secrets`)
- **Token security:** SHA-256 hashes in DB, raw tokens only in email bodies
- **Password hashing:** bcrypt via passlib
- **Naming:** `snake_case` functions, `UPPER_SNAKE_CASE` constants

### Frontend (TypeScript/React)

- **Components:** shadcn/ui, Tailwind CSS classes
- **State:** React context (useAuth), no Redux/Zustand
- **API client:** fetch-based `request<T>()` in `lib/api.ts`
- **Routing:** react-router-dom v6

## Deployment

### Staging

- **URL:** https://tracking-success.stage.jonaskrauss.de
- **Server:** Hetzner VPS `2.28.10.60` (cpx22, fsn1)
- **SSH:** `root@2.28.10.60 -i ~/.ssh/hermine_deploy`
- **Deploy:** rsync code → `docker compose -f docker-compose.staging.yml up -d --build`
- **DB:** PostgreSQL in Docker volume (ephemeral)

### Production

- **URL:** https://tracking-success.jonaskrauss.de
- **Server:** Hetzner VPS `167.233.126.82` (jonaskrauss-de-prod)
- **SSH:** `root@167.233.126.82 -i ~/.ssh/hermine_deploy`
- **Deploy:** rsync code → `docker compose up -d --build` in `/opt/prod/tracking-success/`
- **Network:** `prod_prod-net` (shared Traefik)
- **DB:** PostgreSQL in Docker volume (persistent — NEVER delete without explicit user approval)

### Schema Migrations

- **NEVER** delete the DB volume for schema changes — use `ALTER TABLE` instead
- `Base.metadata.create_all()` only creates new tables, does not alter existing ones
- For adding columns: `ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT false;`

## Email (Sweego)

- **API:** `POST https://api.sweego.io/send` with `Api-Key` header
- **Sender:** `noreply@support.jonaskrauss.de`
- **1Password:** `op://hermine/sweego-api-key/credential`
- **Config:** `SWEEGO_API_KEY` and `APP_BASE_URL` in `.env`, passed via `env_file` in docker-compose

## Testing

```bash
cd backend
source .venv/bin/activate
export DATABASE_URL="sqlite+aiosqlite:///tmp/test_auth.db"
export JWT_SECRET="test-secret"
export SWEEGO_API_KEY="test-key"
export APP_BASE_URL="http://test"
mkdir -p tmp
python -m pytest -v
```

- **TDD:** write failing test first, then implement
- **Test DB:** SQLite via aiosqlite (fast, no Docker needed)
- **48 tests** (16 auth flows + 32 metrics/fasting)
- **Frontend:** no test framework yet (TypeScript compiler is the gate)

## Security Notes

- Tokens stored as SHA-256 hashes (never plaintext)
- CORS restricted to actual origins (not `*`)
- `is_active` gate on login and forgot-password
- Sibling reset tokens invalidated on password reset
- Email sending is fire-and-forget (logged, not blocking registration)
- Rate limiting: not implemented (future work)

## Pitfalls

1. **DB volume deletion destroys all data.** Always use `ALTER TABLE` for schema changes.
2. **`env_file` in docker-compose.yml** must be present for SWEEGO_API_KEY to reach the container. Verify with `docker exec <container> env | grep SWEEGO`.
3. **Sweego 401** = API key not set in container. Check `.env` file + `env_file` directive + `docker compose config`.
4. **TypeScript builds** run in Docker (`pnpm build` = `tsc -b && vite build`). Any TS error blocks the frontend container.
5. **SQLite vs PostgreSQL** — tests use SQLite (fast), production uses PostgreSQL. Column types must be compatible with both.