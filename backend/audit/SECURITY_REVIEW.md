# Security Review

**Date:** 2026-06-09
**Scope:** Authentication, authorization, input validation, CORS, dependency security

---

## Authentication

| Aspect | Status | Details |
|--------|--------|---------|
| JWT algorithm | ✅ | HS256 (configurable) |
| Access token expiry | ✅ | 30 minutes |
| Refresh token expiry | ✅ | 7 days |
| Password hashing | ✅ | bcrypt via passlib |
| JWT library | ⚠️ | `python-jose` (unmaintained since 2021) |
| Secret key default | ❌ | Hardcoded `"change-me-in-production"` |

### Issue S1: Hardcoded default secret key (High)
- `backend/app/core/config.py:48` defaults to `"change-me-me-in-production"` (note: typo "change-me-me" — double "me")
- If deployed without setting `SECRET_KEY` in `.env`, JWT tokens can be forged
- **Fix:** Add validation that raises a startup error if secret key is the default

### Issue S2: python-jose is unmaintained (Medium)
- `python-jose` has not been updated since 2021
- Known CVEs may exist for the `cryptography`-dependent version in use
- **Recommendation:** Migrate to `PyJWT` or `python-jose[cryptography]` → `PyJWT` with proper validation

### Issue S3: Token refresh not revocation-checked (Low)
- No token blacklist or revocation mechanism
- Stolen refresh tokens remain valid for 7 days
- **Recommendation:** Add a token blacklist in Redis (when available) or database

## Authorization

| Aspect | Status |
|--------|--------|
| Role-based access | ❌ Not implemented |
| Endpoint protection | ⚠️ Most endpoints are unprotected (open API) |
| Admin endpoints | ❌ No admin scope |
| API key for collectors | ⚠️ Single collectors API key, no per-source keys |

### Issue S4: No authorization framework (High)
- All prediction/ranking/simulation endpoints are publicly accessible
- No concept of user roles or API scopes
- If the forecast engine is consumer-facing this is acceptable; if B2B, authorization is required
- **Note:** This may be by design for a public forecast tool

## Input Validation

| Aspect | Status |
|--------|--------|
| Pydantic models | ✅ Used throughout API layer |
| SQL injection | ✅ SQLAlchemy ORM — parameterized queries |
| Path traversal | ✅ No file serving from user input |
| XSS | ✅ CSP headers restrict script-src to 'self' |

### Issue S5: Missing request size limits (Low)
- No `max_request_size` middleware configured
- Large payloads could cause memory exhaustion
- **Recommendation:** Add `starlette.middleware.MaxSizeMiddleware` (or equivalent)

## HTTP Security Headers

| Header | Value | Status |
|--------|-------|--------|
| X-Frame-Options | `DENY` | ✅ |
| X-Content-Type-Options | `nosniff` | ✅ |
| Referrer-Policy | `strict-origin-when-cross-origin` | ✅ |
| X-XSS-Protection | `1; mode=block` | ✅ |
| Content-Security-Policy | `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'` | ✅ |
| Strict-Transport-Security | `max-age=31536000; includeSubDomains` | ✅ |

## CORS

| Aspect | Status |
|--------|--------|
| Explicit origins | ✅ `cors_origins` from env, no wildcard |
| Credentials | ✅ `allow_credentials=True` |
| Methods restricted | ✅ GET, POST, PUT, PATCH, DELETE, OPTIONS |
| Headers restricted | ✅ Authorization, Content-Type, X-Request-ID |

## Rate Limiting

| Aspect | Status |
|--------|--------|
| API rate limiting | ❌ Not implemented for HTTP endpoints |
| Collector rate limiting | ✅ 5 req/s (only for data collection, not API) |
| Auth endpoint rate limiting | ❌ Not implemented |

### Issue S6: No API rate limiting (Medium)
- No rate limiting on any HTTP API endpoint
- An attacker can issue unlimited requests
- **Recommendation:** Add `slowapi` or custom token-bucket middleware, even for unauthenticated endpoints

## Secret Management

| Aspect | Status |
|--------|--------|
| .env file | ✅ Used for configuration |
| Default overrides | ✅ pydantic-settings loads from .env |
| Secret rotation | ❌ No mechanism |
| Vault/HSM | ❌ Not integrated |

## Recommendations

1. **Fix hardcoded secret key** — add startup validation that rejects the default value
2. **Migrate from python-jose to PyJWT** — actively maintained, wider adoption
3. **Add rate limiting** — at minimum on auth and simulation endpoints
4. **Add request size limits** — configure `MaxSizeMiddleware`
5. **Consider adding API authentication** if the service should be non-public
6. **Add token blacklist** for refresh token revocation
