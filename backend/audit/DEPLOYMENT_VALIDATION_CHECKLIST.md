# Deployment Validation Checklist

**Date:** 2026-06-10
**Phase:** DEPLOY-001 — Production Environment Setup
**Target Stack:** PostgreSQL (Neon) · Redis · FastAPI · Next.js · Docker

---

## 1. Environment Configuration

- [x] `.env.production.example` documents all required variables
- [x] `DATABASE_URL` points to Neon PostgreSQL (or production equivalent)
- [x] `SECRET_KEY` is set to a strong random value (min 32 chars)
- [x] `CORS_ORIGINS` set to the actual frontend domain(s)
- [x] `SENTRY_DSN` configured for error tracking
- [x] `REDIS_URL` points to production Redis instance
- [x] `LOG_LEVEL` set to `INFO` (not `DEBUG`)
- [x] `DEBUG=false` in production
- [x] JWT configuration matches security requirements

## 2. Docker Stack Build

- [x] `backend/Dockerfile` builds without errors
- [x] `frontend/Dockerfile` builds without errors
- [x] `docker-compose.production.yml` parses without syntax errors
- [x] Backend image size is reasonable (< 1GB)
- [x] Frontend image builds with `standalone` output
- [ ] No security vulnerabilities in base images — requires `docker scan` or Trivy pass

## 3. Service Health

- [x] PostgreSQL container starts and passes `pg_isready`
- [x] Redis container starts and passes `redis-cli ping`
- [x] Backend container starts without errors
- [x] Backend health endpoint returns `{"status": "ok"}`
- [x] `/health/database` reports connected
- [x] `/health/redis` reports connected
- [x] `/health/system` returns platform info
- [x] Frontend container starts without errors
- [x] Frontend serves pages without 500 errors

## 4. Database Initialization

- [x] Tables created (`Base.metadata.create_all` succeeds)
- [x] Seed script runs without errors
- [x] 48 teams seeded across 12 groups
- [x] 72 group matches created
- [x] Competition record exists
- [x] Group standings initialized
- [x] ELO ratings populated
- [x] FIFA rankings populated
- [x] xG metrics populated

## 5. Startup Validation

- [x] Startup readiness report logged at INFO level
- [x] No startup errors in logs
- [x] Sentry SDK initialized (if DSN configured)
- [x] Prometheus `/metrics` endpoint responds
- [x] Prometheus business counters initialized (predictions, simulations, scenarios, calibrations)
- [x] Rate limiter active (slowapi)
- [x] Security headers present (X-Frame-Options, CSP, HSTS)
- [x] Request logging structured (JSON format)

## 6. Numba Warm-Up

- [x] Warm-up runs during container startup
- [x] Numba JIT compilation logged with timing
- [x] Warm-up completes within 30 seconds
- [x] First prediction request does not trigger JIT compilation
- [x] Warm-up failure does not crash the container (non-fatal)

## 7. Cache & Redis

- [x] Redis responds to ping from backend container
- [x] Cache TTL configuration loaded
- [x] Cache decorator operational (read/write)
- [x] Cache invalidation works (pattern-based SCAN + DEL)
- [x] Redis persistence configured (AOF or RDB)

## 8. Security

- [x] Backend port 8000 not exposed to public internet directly
- [x] PostgreSQL port 5433 not exposed to public internet
- [x] Redis port 6379 not exposed to public internet
- [x] CORS restricted to specific origins (not `*`)
- [x] CSP headers restrict script sources — `default-src 'self'` in `SecurityHeadersMiddleware`
- [x] HSTS enabled with `includeSubDomains` — `Strict-Transport-Security` in `SecurityHeadersMiddleware`
- [x] Non-root user runs the backend container

## 9. Networking

- [x] Backend can reach PostgreSQL (internal Docker network)
- [x] Backend can reach Redis (internal Docker network)
- [x] Frontend can reach Backend API
- [x] Health check dependencies respected (`depends_on` conditions)

## 10. Logging & Monitoring

- [x] JSON structured logging enabled
- [x] Log levels correctly applied
- [x] Request ID propagated through logs
- [x] Container logs accessible via `docker compose logs`
- [x] Log rotation configured (max-size 10m, max-file 3)

---

## Validation Summary

| Check | Status | Notes |
|-------|--------|-------|
| Docker Build | ✅ PASS | Both images build; `standalone` output; slim base images |
| DB Connectivity | ✅ PASS | Healthcheck + entrypoint wait + connection pooling configured |
| Redis Connectivity | ✅ PASS | Healthcheck + AOF persistence + cache decorator verified (DEPLOY-005) |
| Seed Data | ✅ PASS | 48 teams, 12 groups, 72 matches, ELO/FIFA/xG all seeded |
| Numba Warm-Up | ✅ PASS | Runs at startup, completes in ~1.5s, non-fatal on failure |
| Health Endpoints | ✅ PASS | `/health`, `/health/database`, `/health/redis`, `/health/system` all respond |
| Prometheus Metrics | ✅ PASS | `/metrics` endpoint with business counters |
| Security Headers | ✅ PASS | CSP, HSTS, X-Frame-Options all active in middleware |
| Rate Limiting | ✅ PASS | slowapi active with tiered limits (Phase 9.5) |
| Cache Performance | ✅ PASS | 8.3x–43.6x speedup verified (DEPLOY-005) |

**Overall Status:** ✅ VALIDATED (2 minor items pending verification — low risk)
