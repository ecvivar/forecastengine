# Deployment Guide — WorldCup Forecast Engine 2026

**Date:** 2026-06-10 | **Version:** 1.1.0

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Backend — Render](#2-backend--render)
3. [Frontend — Vercel](#3-frontend--vercel)
4. [Environment Variables](#4-environment-variables)
5. [Changes Applied](#5-changes-applied)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Architecture Overview

```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐
│   Vercel    │ ───> │  Render      │ ───> │  Neon/DB     │
│  Frontend   │      │  Backend     │      │  PostgreSQL  │
│  (Next.js)  │      │  (FastAPI)   │      │              │
└─────────────┘      └──────────────┘      └──────────────┘
                           │
                           v
                     ┌──────────────┐
                     │  Upstash     │
                     │  Redis       │
                     │  (optional)  │
                     └──────────────┘
```

- **Frontend:** Next.js 14 (SSG) → Vercel
- **Backend:** FastAPI + Gunicorn → Render (Docker)
- **Database:** PostgreSQL 16 → Neon (or Render Managed Postgres)
- **Cache:** Redis 7 (optional) → Upstash (or Render Managed Redis)

---

## 2. Backend — Render

### 2.1 Prerequisites

- Render account connected to your GitHub repo
- The `render.yaml` blueprint at the project root

### 2.2 Deploy via Blueprint (recommended)

1. In Render Dashboard → **Blueprints** → **New Blueprint**
2. Connect your repository
3. Render reads `render.yaml` and auto-creates:
   - `wc2026-db` — PostgreSQL 16
   - `wc2026-backend` — Docker web service
   - `wc2026-frontend` — Docker web service (if desired)
4. After creation, update env vars:
   - `CORS_ORIGINS` → your frontend domain
   - `NEXT_PUBLIC_API_URL` → your backend domain
   - `REDIS_URL` and `SENTRY_DSN` (optional)

### 2.3 Deploy via Dashboard (manual)

1. **Database:** Create a new PostgreSQL in Render
2. **Web Service:**
   - Type: **Docker**
   - Name: `wc2026-backend`
   - Root Directory: `backend`
   - Dockerfile Path: `./backend/Dockerfile`
   - Health Check Path: `/health`
   - Env vars: see section 4

### 2.4 What the Startup Does

On container start, `docker-entrypoint.sh` runs:

1. Waits for PostgreSQL (up to 60s)
2. Creates tables via `Base.metadata.create_all()`
3. Seeds initial data (48 teams, 12 groups, 72 matches — idempotent)
4. Starts Numba JIT warm-up in **background** (non-blocking)
5. Starts Gunicorn with Uvicorn workers on `$PORT` (Render dynamic port)

---

## 3. Frontend — Vercel

### 3.1 Prerequisites

- Vercel account connected to your GitHub repo
- Frontend code in `frontend/` directory

### 3.2 Deploy Steps

```bash
# Install Vercel CLI (optional, can also use Vercel Dashboard)
npm i -g vercel

# From the project root, deploy
cd frontend
vercel --prod

# Set environment variable
vercel env add NEXT_PUBLIC_API_URL https://your-backend.onrender.com/api/v1
```

Or connect your GitHub repo in Vercel Dashboard:
- **Framework Preset:** Next.js
- **Root Directory:** `frontend`
- **Build Command:** `next build` (default)
- **Output Directory:** `.next` (default)
- **Environment Variables:**
  - `NEXT_PUBLIC_API_URL` = `https://your-backend.onrender.com/api/v1`

### 3.3 Important Notes

- All pages use `"use client"` — data fetching is client-side via API calls
- The build generates static pages (SSG) that are served as static assets
- Vercel serves the JS bundles; the backend handles all computation
- No `.vercel.json` needed — defaults work fine

---

## 4. Environment Variables

### 4.1 Backend (Render)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string (`postgresql+psycopg2://...`) |
| `SECRET_KEY` | ✅ | JWT signing key (min 32 chars). Generate: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `CORS_ORIGINS` | ✅ | Frontend domain(s), comma-separated |
| `REDIS_URL` | ❌ | Redis connection string (optional, caching disabled if absent) |
| `SENTRY_DSN` | ❌ | Sentry project DSN (optional) |
| `LOG_LEVEL` | ❌ | Default: `INFO` |
| `DB_POOL_SIZE` | ❌ | Default: `10` |
| `DB_MAX_OVERFLOW` | ❌ | Default: `20` |
| `ENGINE_DEFAULT_SIMULATIONS` | ❌ | Default: `100000` |
| `WEB_CONCURRENCY` | ❌ | Gunicorn workers (Render auto-sets to 1 on free tier) |

### 4.2 Frontend (Vercel)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | ✅ | Backend API URL with `/api/v1` suffix, e.g., `https://api.onrender.com/api/v1` |

---

## 5. Changes Applied

### 5.1 Backend — Render Optimizations

| Change | File | Why |
|--------|------|-----|
| Fixed psycopg2 dialect | `backend/app/core/config.py:16` | URL used `+psycopg` (v3) but driver was `psycopg2-binary` |
| Dynamic port binding | `backend/docker-entrypoint.sh` | Render assigns `$PORT` dynamically; fallback to `8000` |
| `--forwarded-allow-ips='*'` | `backend/docker-entrypoint.sh` | Correct client IP behind Render proxy |
| Non-blocking Numba warm-up | `backend/docker-entrypoint.sh` | Runs via `nohup ... &` so Gunicorn starts immediately |
| Added missing model imports | `backend/docker-entrypoint.sh` | Seed script needed `Player` and `simulation` module for SQLAlchemy registry |
| Removed duplicate `create_all` | `backend/app/main.py` | Tables already created in entrypoint |
| Fixed Content-Security-Policy | `backend/app/core/middleware.py:20` | Added `cdn.jsdelivr.net` and `'unsafe-inline'` for Swagger UI |
| Added `scikit-learn` | `backend/requirements*.txt` | Missing dependency for `calibration_refinement.py` |
| Added `starlette` | `backend/requirements*.txt` | Directly imported but not listed |
| `requirements-prod.txt` | `backend/` | Stripped test/dev deps for leaner Docker image |
| Optimized Dockerfile | `backend/Dockerfile` | Uses `requirements-prod.txt`, removes `--user` pip flag (caused import errors as non-root user) |

### 5.2 Frontend — Vercel Fix

| Change | File | Why |
|--------|------|-----|
| Removed `@next/swc-win32-x64-msvc` | `frontend/package.json` | Windows-native SWC binary at version `^16.2.7` — doesn't exist on Linux and mismatched Next.js 14 |

### 5.3 New Files

| File | Purpose |
|------|---------|
| `render.yaml` | Render blueprint — defines backend, frontend, and PostgreSQL |
| `backend/requirements-prod.txt` | Production-only Python dependencies |

---

## 6. Troubleshooting

### 6.1 Backend

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: No module named 'sqlalchemy'` | `pip --user` installs to `/root/.local/` but container runs as `app` user | Removed `--user` flag from Dockerfile |
| `ModuleNotFoundError: No module named 'sklearn'` | Missing dependency | Added `scikit-learn` to requirements |
| `expression 'Player' / 'SimulationResult' failed to locate a name` | SQLAlchemy registry missing model class | Import all referenced models before first query |
| `/docs` shows blank page | CSP blocking Swagger UI CDN + inline scripts | Added `cdn.jsdelivr.net` and `'unsafe-inline'` to CSP |
| `No open HTTP ports detected` | Port scan before Gunicorn binds | Normal — resolves automatically |
| Container exits immediately | Wrong `DATABASE_URL` scheme or missing env vars | Check `postgresql+psycopg2://` format and required vars |

### 6.2 Frontend

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Command "npm install" exited with 1` | Windows-native SWC binary in `package.json` | Remove `@next/swc-win32-x64-msvc` from dependencies |
| Pages show no data | Wrong `NEXT_PUBLIC_API_URL` or CORS | Verify URL ends with `/api/v1` and `CORS_ORIGINS` includes frontend domain |
| 502 Bad Gateway | Backend not ready | Wait for startup (~30s), check Render logs |

### 6.3 Health Endpoints

```bash
# Backend health
curl https://your-backend.onrender.com/health
curl https://your-backend.onrender.com/health/database
curl https://your-backend.onrender.com/health/redis
curl https://your-backend.onrender.com/metrics

# API
curl https://your-backend.onrender.com/docs       # Swagger UI
curl https://your-backend.onrender.com/api/v1/teams
```

---

## Quick Reference

```bash
# Backend — Render
#   Push to main → auto-deploy via GitHub integration
#   Or manual: Render Dashboard → Manual Deploy

# Frontend — Vercel
cd frontend
vercel --prod

# Local build test
cd backend && docker build -t wc2026-backend .
cd frontend && npm run build
```
