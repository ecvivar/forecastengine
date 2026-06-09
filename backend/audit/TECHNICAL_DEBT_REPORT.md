# Technical Debt Report

**Date:** 2026-06-09
**Scope:** Code quality concerns, deprecated APIs, hardcoded values, tech debt items

---

## Pydantic Protected Namespace Warning

**File:** `backend/app/schemas/comparison.py` (and any schema with field named `model_name`)
**Severity:** Low
**Details:**
```
Field "model_name" in ModelComparisonMetricResponse has conflict with protected namespace "model_".
```
Pydantic v2 reserves `model_` prefix for internal use. Fields named `model_name` trigger a deprecation warning.

**Fix:** Rename field to `model_name_` with `alias="model_name"`, or set `model_config['protected_namespaces'] = ()` on the schema class.

---

## Deprecated `@app.on_event("startup")`

**File:** `backend/app/main.py:86`
**Severity:** Low
**Details:** The `@app.on_event("startup")` and `@app.on_event("shutdown")` decorators are deprecated in FastAPI/Starlette. The recommended approach is the `lifespan` context manager pattern.

**Fix:** Replace:
```python
@app.on_event("startup")
async def startup():
    ...
@app.on_event("shutdown")
async def shutdown():
    ...
```
with:
```python
from contextlib import asynccontextmanager
@asynccontextmanager
async def lifespan(app):
    # startup
    yield
    # shutdown
app = FastAPI(lifespan=lifespan)
```

---

## Hardcoded Default Secret Key

**File:** `backend/app/core/config.py:48`
**Severity:** Critical
**Details:** `secret_key` defaults to `"change-me-me-in-production"` — note the double "me" typo. If deployed without overriding through `.env`, all JWT tokens can be forged.

**Fix:** Add a Pydantic `@field_validator("secret_key")` that raises on the default value, forcing production deployments to set `SECRET_KEY` in `.env`.

---

## Static Historical Match Data

**File:** `backend/app/data/historical_matches.py`
**Severity:** High
**Details:** All 192 historical matches are hardcoded as a Python list. Any update (adding 2026 World Cup data) requires a code deployment.

**Fix:** Migrate to a database table with a seed migration and an admin refresh endpoint.

---

## In-Memory-Only Metrics

**File:** `backend/app/core/metrics.py`
**Severity:** Medium
**Details:** Request counts, durations, cache hit rates are stored only in process memory. All data is lost on restart. No historical trending possible.

**Fix:** Option 1: Export to Prometheus push gateway. Option 2: Periodically snapshot to database. Option 3: Add structured metric log lines (statsd-compatible).

---

## No API Rate Limiting

**File:** `backend/app/core/middleware.py` (no rate limiter exists)
**Severity:** Medium
**Details:** No request throttling on any HTTP API endpoint. Rate limiter only exists on data collectors (`app/collectors/base.py:23`).

**Fix:** Add `slowapi` or custom token-bucket middleware to FastAPI app.

---

## No Log Rotation

**File:** `backend/app/core/logging.py` (no file handler configured)
**Severity:** Low
**Details:** Logging goes to stderr/stdout only. Acceptable in containerized deployments but no retention policy.

**Fix:** Add `RotatingFileHandler` or confirm container log rotation is configured externally.

---

## Benchmark Known Issues

### Redis URL parse error
**File:** `backend/audit/benchmark_performance.py`
**Severity:** Low (benchmark-only)
**Details:** Setting `REDIS_URL=""` caused `ValueError: Redis URL must specify one of the following schemes`. Fixed by using `"redis://localhost:6379/0"` but this causes connection errors (handled gracefully). Cache still unavailable in benchmark — impacts API timing.

### Models not imported for SQLite test
**File:** `backend/audit/benchmark_performance.py` (was broken, now fixed)
**Details:** SQLAlchemy mapper failed to resolve `Group.competition` relationship because model modules weren't imported. Fixed by mirroring `conftest.py` model imports.

---

## Summary

| Category | Items | Critical | High | Medium | Low |
|----------|-------|----------|------|--------|-----|
| Security | 2 | 1 | 0 | 1 | 0 |
| Data | 1 | 0 | 1 | 0 | 0 |
| Observability | 2 | 0 | 0 | 1 | 1 |
| Code quality | 3 | 0 | 0 | 0 | 3 |
| Infrastructure | 1 | 0 | 0 | 1 | 0 |
| **Total** | **9** | **1** | **1** | **3** | **4** |

## Quick Wins (30-min fixes)

1. Suppress Pydantic protected namespace warning — `model_config['protected_namespaces'] = ()`
2. Fix secret key typo → `"change-me-in-production"` + add validator
3. Add rate limiting middleware (slowapi or custom)
4. Switch from `@app.on_event` to `lifespan` pattern

## Strategic Items (1-3 day efforts)

1. Migrate historical data to database (3 days)
2. Add Sentry APM integration (1 day)
3. Migrate to PyJWT (1 day)
4. Add metric persistence (2 days)
