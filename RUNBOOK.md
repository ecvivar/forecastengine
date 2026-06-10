# DEPLOY-007: Runbook — WorldCup Forecast Engine 2026

**Version:** 1.1.0
**Date:** 2026-06-10
**Applies to:** Production deployment (Docker Compose / Render)

---

## 1. Deployment

### 1.1 Environment Variables

Copy the template and fill all required values:

```bash
cp .env.production.example .env
```

**Required variables:**

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Neon PostgreSQL connection string | `postgresql+psycopg2://user:pass@host:5432/worldcup_forecast` |
| `SECRET_KEY` | JWT signing key (min 32 chars) | Generate: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `CORS_ORIGINS` | Allowed frontend origins | `https://your-domain.com` |

**Strongly recommended:**

| Variable | Description |
|----------|-------------|
| `SENTRY_DSN` | Sentry project DSN for error tracking |
| `REDIS_URL` | Redis connection string (caching works without it but disabled) |

**Optional (defaults shown):**

```bash
LOG_LEVEL=INFO
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
CACHE_TTL=300
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
ENGINE_DEFAULT_SIMULATIONS=100000
DEBUG=false
```

### 1.2 Neon (PostgreSQL) Setup

1. Create a project at [neon.tech](https://neon.tech)
2. Select region closest to your users
3. Copy the connection string (use `psycopg2` driver):
   ```
   postgresql+psycopg2://user:pass@ep-xxx.us-east-2.aws.neon.tech/worldcup_forecast
   ```
4. Set `DATABASE_URL` in `.env`
5. Recommended Neon settings:
   - Autosuspend: off (production)
   - Pooled connection: enabled
   - Min CPU: 0.25, Max CPU: 2 (auto-scale)

### 1.3 Redis Setup

**Option A: Upstash (serverless, recommended)**
1. Create a database at [upstash.com](https://upstash.com)
2. Select region matching your backend
3. Copy `UPSTASH_REDIS_REST_URL`
4. Set `REDIS_URL=redis://default:pass@host:6379`

**Option B: Self-hosted Docker (for single-node deployments)**
```bash
docker run -d --name wc2026-redis \
  -p 6379:6379 \
  -v redis_data:/data \
  redis:7-alpine \
  redis-server --appendonly yes --save 60 1
```

### 1.4 Docker Deployment

```bash
# Build and start all services
docker compose -f docker-compose.production.yml up -d --build

# Check startup logs
docker compose -f docker-compose.production.yml logs -f backend

# Verify health
curl http://localhost:8000/health
curl http://localhost:8000/health/database
curl http://localhost:8000/health/redis
```

**Expected startup sequence:**
1. PostgreSQL container starts (5-10s)
2. Redis container starts (2-3s)
3. Backend container starts:
   - Waits for PostgreSQL (up to 60s)
   - Creates database tables
   - Seeds initial data (idempotent — skips if data exists)
   - Starts background Numba JIT warm-up (non-blocking)
   - Starts Gunicorn immediately on port `$PORT` (default `8000`)
4. Frontend container starts (depends on backend)

### 1.5 Render Deployment

**Prerequisites:** A Render account connected to your GitHub/GitLab repo.

**Option A: Blueprint (render.yaml) — Recommended**

The repository includes a `render.yaml` blueprint at the project root. Connect your repo to Render and it auto-detects the file:

1. In Render Dashboard → **Blueprints** → **New Blueprint**
2. Connect your repository
3. Render reads `render.yaml` and creates:
   - `wc2026-db` — PostgreSQL 16 database
   - `wc2026-backend` — Docker web service on port `$PORT`
   - `wc2026-frontend` — Docker web service
4. After creation:
   - Update `CORS_ORIGINS` in backend env vars to your actual frontend domain
   - Update `NEXT_PUBLIC_API_URL` in frontend env vars to your actual backend domain
   - Set `REDIS_URL` and `SENTRY_DSN` if applicable

**Option B: Manual setup via Render Dashboard**

1. **Database:** Create a new PostgreSQL database in Render (free tier available)
2. **Backend Web Service:**
   - Type: **Docker**
   - Name: `wc2026-backend`
   - Root Directory: `backend`
   - Dockerfile Path: `./backend/Dockerfile`
   - Health Check Path: `/health`
   - Env vars: set `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`
3. **Frontend Web Service:**
   - Type: **Docker**
   - Name: `wc2026-frontend`
   - Root Directory: `frontend`
   - Dockerfile Path: `./frontend/Dockerfile`
   - Env vars: set `NEXT_PUBLIC_API_URL`

> **Note:** Render passes `$PORT` dynamically. The entrypoint binds to `$PORT` (fallback `8000`). No port configuration needed.

### 1.6 Vercel (Frontend) Deployment

The frontend is configured for Docker deployment (`output: "standalone"`), but can also be deployed to Vercel:

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel --prod

# Set environment variable
vercel env add NEXT_PUBLIC_API_URL https://your-api-domain.com/api/v1
```

**Note:** All pages are `"use client"` — data fetching happens client-side via API calls. Vercel serves the static JS bundles; the backend handles all computation.

---

## 2. Startup

### 2.1 Database Migrations

Tables are created automatically by the Docker entrypoint **before** Gunicorn starts. This is the single point of schema initialization — the app lifespan no longer calls `create_all()`.

```bash
# docker-entrypoint.sh — runs once at container start:
python -c "
from app.db.session import engine, Base
from app.models import ...
Base.metadata.create_all(bind=engine)
"
```

For schema changes, update models and redeploy. `create_all` is idempotent (adds new columns/tables, never drops). For destructive changes, run a manual migration:

```bash
# Enter the container
docker exec -it wc2026-backend bash

# Run migration script
python -c "
from app.db.session import engine, Base
from app.models import team, match, group, group_standing, competition, elo_rating, fifa_ranking, player, simulation, xg_metrics
Base.metadata.create_all(bind=engine)
print('Migration complete')
"
```

### 2.2 Seed Process

Seed data is baked into `docker-entrypoint.sh`. It:

1. Checks if a `Competition` record exists
2. If none found, seeds 48 teams across 12 groups (A-L)
3. Creates ELO ratings, FIFA rankings, and xG metrics for each team
4. Creates 72 group-stage matches
5. If data exists, skips seeding (idempotent)

To manually re-seed:
```bash
docker exec -it wc2026-backend python -c "
from app.db.session import SessionLocal, engine, Base
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print('DB reset — restart container to re-seed')
"
docker restart wc2026-backend
```

### 2.3 Numba Warm-Up

The entrypoint launches `warmup_numba()` as a **background process** (`nohup ... &`) so it does **not block** server startup. It runs 3 iterations of `run_single_tournament_py()` with an 8-team mock tournament.

**Expected output in logs:**
```
Starting background Numba warm-up...
Numba warm-up: compiling JIT functions...
=== Starting Gunicorn with 4 worker(s) on port 8000... ===
Numba warm-up complete in ~1500ms
```

**If warm-up fails:** The error is logged to `/tmp/numba_warmup.log`. The first prediction request may pay the JIT compilation penalty (~2-3s).

**Why background?** Render's health check may fire before JIT finishes. Running warm-up in parallel with Gunicorn startup ensures the server responds immediately.

---

## 3. Monitoring

### 3.1 Health Endpoints

| Endpoint | Response | Purpose |
|----------|----------|---------|
| `GET /health` | `{"status":"ok", "version":"1.0.0"}` | Basic liveness |
| `GET /health/database` | `{"status":"ok", "database":"connected"}` | DB connectivity |
| `GET /health/redis` | `{"status":"ok", "redis":"connected"}` | Cache connectivity |
| `GET /health/system` | `{"python_version":"...","cpu_count":N}` | System info |

**Docker HEALTHCHECK** runs every 10s against `/health` with 5 retries and 15s start period.

**Client IP detection:** Gunicorn is started with `--forwarded-allow-ips='*'` to correctly report real client IPs behind Render's proxy. On Docker Compose (direct traffic), this has no effect.

### 3.2 Prometheus Metrics

Endpoints at `GET /metrics`:

**Business counters:**
- `predictions_total` — prediction requests
- `simulations_total` — simulation runs
- `scenarios_total` — what-if scenarios
- `calibrations_total` — calibration runs

**System metrics:**
- Request duration histograms
- Active request gauge
- Python GC metrics

**Scrape configuration (prometheus.yml):**
```yaml
scrape_configs:
  - job_name: 'wc2026-backend'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### 3.3 Logs

**Format:** JSON structured logging

```json
{"timestamp": "...", "level": "INFO", "request_id": "abc123", "message": "Prediction computed", "duration_ms": 9.3}
```

**Log levels in production:** `INFO` (set via `LOG_LEVEL` env var)

**Access logs:** Nginx or reverse proxy handles access logging; the app logs only business events.

**Docker log access:**
```bash
docker compose -f docker-compose.production.yml logs -f --tail=100 backend
```

---

## 4. Incident Response

### 4.1 Redis Unavailable

**Symptoms:**
- `/health/redis` returns error
- Backend logs: `Cache unavailable — falling back to direct DB queries`
- APIs still work but are slower

**Impact:** Performance degradation (no caching). All functionality preserved.

**Response:**
```bash
# 1. Check Redis container
docker inspect wc2026-redis --format '{{.State.Status}}'

# 2. Restart Redis
docker compose -f docker-compose.production.yml restart redis

# 3. Verify
curl http://localhost:8000/health/redis

# 4. If persistent — check Redis logs
docker compose -f docker-compose.production.yml logs redis

# 5. If data corruption — clear and restart
docker compose -f docker-compose.production.yml down redis
docker volume rm wc2026_redis_data_prod
docker compose -f docker-compose.production.yml up -d redis

# 6. Consider failing over to Upstash (update REDIS_URL, restart backend)
```

### 4.2 PostgreSQL Unavailable

**Symptoms:**
- `/health/database` returns error
- Backend logs: `Could not connect to PostgreSQL`
- All data-dependent endpoints return 500

**Impact:** Complete service unavailability for all API endpoints.

**Response:**
```bash
# 1. Check Neon status dashboard
#    https://status.neon.tech

# 2. Check connection string
#    Verify DATABASE_URL in .env is correct

# 3. Test connection manually
docker exec -it wc2026-backend python -c "
from sqlalchemy import create_engine, text
engine = create_engine('$DATABASE_URL')
engine.connect().execute(text('SELECT 1'))
print('OK')
"

# 4. If connection pool exhausted — restart backend
docker compose -f docker-compose.production.yml restart backend

# 5. If permanent failure — update DATABASE_URL to failover replica
#    Edit .env → docker compose restart backend
```

### 4.3 API High Latency

**Symptoms:**
- P95 latency > 500ms on health/alerts
- User complaints about slow pages

**Response:**
```bash
# 1. Check metrics
curl http://localhost:8000/metrics | grep request_duration

# 2. Check for N+1 queries (DB audit identified 2 endpoints)
#    - GET /api/v1/predictions (101 queries)
#    - POST /api/v1/scenarios/simulate (97 queries)

# 3. Check Redis cache hit rate
docker exec -it wc2026-redis redis-cli INFO stats | grep hit

# 4. Check CPU/memory
docker stats wc2026-backend --no-stream

# 5. If worker saturation — increase worker count
#    Edit docker-compose.production.yml:
#    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
#    docker compose -f docker-compose.production.yml up -d backend

# 6. If DB bottleneck — check Neon compute metrics
#    Scale Neon compute: increase min CPU / max CPU
```

### 4.4 Failed Deployment

**Symptoms:**
- Container exits immediately on `docker compose up`
- Health checks fail repeatedly
- Frontend shows 502/504 errors

**Response:**
```bash
# 1. Check container logs
docker compose -f docker-compose.production.yml logs backend --tail=100

# 2. Common causes:
#    a) Missing environment variable
#       → Check .env has all required vars
#    b) Database connection timeout
#       → Check DATABASE_URL, network, firewall
#    c) Port conflict
#       → Check if ports 8000/3000 are available: netstat -ano | findstr :8000

# 3. Roll back to previous image
docker compose -f docker-compose.production.yml down
docker compose -f docker-compose.production.yml up -d

# 4. Or use a specific tagged image
docker compose -f docker-compose.production.yml build backend  # rebuild
docker compose -f docker-compose.production.yml up -d backend
```

### 4.5 Rollback Procedure

```bash
# Option A: Revert to previous Docker image tag
# (if using tagged images in CI)
docker compose -f docker-compose.production.yml down
export IMAGE_TAG=v1.0.0-previous
docker compose -f docker-compose.production.yml up -d

# Option B: Revert git commit and redeploy
git log --oneline -5
git revert HEAD --no-edit
docker compose -f docker-compose.production.yml up -d --build

# Verify rollback
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/teams | head -c 200
```

### 4.6 High Error Rate

**Symptoms:**
- >5% HTTP 5xx errors in monitoring
- Sentry alerts firing

**Response:**
```bash
# 1. Check Sentry for recent errors
#    → Identify top error class and stack trace

# 2. Check recent deployment (did something just change?)
git log --oneline -5

# 3. Common patterns:
#    - Rate limit too strict → check slowapi config
#    - Database pool exhaustion → check DB_POOL_SIZE
#    - OOM → check docker stats, reduce workers or increase memory

# 4. Temporary mitigation: increase resources
#    docker compose -f docker-compose.production.yml up -d backend

# 5. Permanent fix: patch, test, redeploy
```

---

## 5. Recovery Procedures

### Full System Recovery (from scratch)

```bash
# 1. Clone repository
git clone https://github.com/your-org/worldcup-forecast-engine.git
cd worldcup-forecast-engine

# 2. Configure environment
cp .env.production.example .env
# Edit .env with production values

# 3. Start stack
docker compose -f docker-compose.production.yml up -d --build

# 4. Verify everything
sleep 15  # wait for startup
curl http://localhost:8000/health && echo "OK"
curl http://localhost:8000/health/database && echo "OK"
curl http://localhost:8000/health/redis && echo "OK"
curl http://localhost:3000 | head -c 100 && echo "Frontend OK"
```

**Expected recovery time:** ~3-5 minutes (Docker pull + build + startup + warm-up)

### Data Recovery

Database data persists in Docker volumes (`pgdata_prod`). To restore from backup:

```bash
# 1. Stop backend
docker compose -f docker-compose.production.yml stop backend

# 2. Restore from Neon backup
#    Neon provides point-in-time recovery — use their dashboard

# 3. Or restore from pg_dump
pg_restore -h localhost -p 5433 -U postgres -d worldcup_forecast backup.dump

# 4. Restart backend
docker compose -f docker-compose.production.yml start backend
```

---

## Quick Reference

```bash
# Service management (Docker Compose)
docker compose -f docker-compose.production.yml up -d          # Start all
docker compose -f docker-compose.production.yml down           # Stop all
docker compose -f docker-compose.production.yml restart <svc>  # Restart one
docker compose -f docker-compose.production.yml logs -f <svc>  # Tail logs

# Service management (Render)
#   Connect repo → Render auto-detects render.yaml
#   Or deploy manually via Dashboard → Web Service → Docker

# Health checks
curl http://localhost:8000/health
curl http://localhost:8000/health/database
curl http://localhost:8000/health/redis
curl http://localhost:3000

# Metrics
curl http://localhost:8000/metrics

# Maintenance
docker exec -it wc2026-backend python -c "..."                # Run Python
docker exec -it wc2026-redis redis-cli                        # Redis CLI
docker exec -it wc2026-db psql -U postgres worldcup_forecast  # SQL CLI
```

---

## Changelog

### v1.1.0 (2026-06-10) — Render deployment optimizations

| Change | File | Reason |
|--------|------|--------|
| Fixed psycopg2 dialect | `config.py` | URL used `+psycopg` (v3) but driver is `psycopg2-binary` — changed to `+psycopg2` |
| Dynamic port binding | `docker-entrypoint.sh` | Render assigns `$PORT` dynamically; fallback to `8000` for Docker Compose |
| Non-blocking Numba warm-up | `docker-entrypoint.sh` | Moved to `nohup ... &` so Gunicorn starts immediately — avoids health check timeout |
| `--forwarded-allow-ips='*'` | `docker-entrypoint.sh` | Correct client IP behind Render proxy |
| Removed duplicate `create_all` | `main.py` | Tables already created in entrypoint; lifespan no longer calls it |
| Removed `asyncpg` | `requirements.txt` | Unused — no async DB code |
| Created `requirements-prod.txt` | `backend/` | Stripped test/dev deps for leaner Docker image |
| Optimized Dockerfile | `Dockerfile` | Uses `requirements-prod.txt`, cleans pip cache |
| Created `render.yaml` | root | Blueprint for Render IaC — one-click deploy |
