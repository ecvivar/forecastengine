# Quality Report — Test Coverage & Code Quality

**Date:** 2026-06-09
**Scope:** Backend test suite (101 tests, 19 test files), frontend build

---

## Test Results Summary

| Metric | Value |
|--------|-------|
| Total tests collected | 101 |
| Passed | 85 |
| Failed | 10 |
| Skipped | 3 |
| Test files | 19 |
| Collection errors | 0 |

## Test Coverage by Module

| Module | Tests | Status |
|--------|-------|--------|
| Health | 5 | ✅ All pass |
| CORS | 3 | ✅ All pass |
| Error handler | 6 | ✅ All pass |
| Exceptions | 10 | ✅ All pass |
| Cache | 7 + 3 skipped | ✅ 7 pass, 3 skip (no Redis) |
| Cache decorator | 2 | ✅ All pass |
| Logging | 6 | ✅ All pass |
| Metrics | 10 | ✅ All pass |
| Security (JWT) | 4 | ✅ All pass |
| Security (password) | 2 | ❌ Both fail |
| Teams | 4 | ✅ All pass |
| IGF | 4 | ✅ All pass |
| Match prediction | 4 | ✅ All pass |
| Full prediction | 6 | ✅ All pass |
| Calibration | 15 | ⚠️ 7 pass, 8 fail |
| Comparison | 2 | ✅ All pass |
| Export | 5 | ✅ All pass |
| Scenarios | 2 | ✅ All pass |

## Failure Analysis

### Calibration failures (8 tests)
- `test_calibrate_returns_report` — likely due to missing model output
- `test_brier_score_perfect` — perfect prediction not scoring 0.0
- `test_log_loss_finite` — log loss returning inf for some cases
- `test_calibration_error_zero_for_perfect` — calibration error not zero
- `test_auc_roc_perfect` — AUC not 1.0 for perfect predictions
- `test_by_tournament` — per-tournament breakdown unstable
- `test_by_stage` — per-stage breakdown unstable
- `test_weight_adjustments` — weight adjustments not changing results
- `test_full_run_with_real_data` — end-to-end run fails

**Root cause:** The calibration engine's `calibrate()` method appears to expect pre-computed model outputs (Elo, DC probabilities) that are not being computed in test scope. Tests that mock or pass real data directly to `CalibrationEngine.calibrate()` will fail without the full prediction pipeline.

**Recommendation:** Fix by providing realistic mock prediction data or by testing via the full prediction → calibration flow (as `test_predict_then_calibrate` does — it passes).

### Password hashing failures (2 tests)
- `test_hash_and_verify` — bcrypt hash not verifiable in test env
- `test_wrong_password` — wrong password incorrectly verified

**Root cause:** `passlib` + `bcrypt` compatibility issue on Python 3.11/3.13. The bcrypt library version is 5.0.0 which changed the return type/API from what passlib expects.

**Recommendation:** Pin `bcrypt<4.1` or upgrade `passlib` to latest. However, if JWT auth is the primary auth mechanism, password hashing may not be critical path.

### Skipped tests (3)
- `test_set_and_get`, `test_invalidate`, `test_flush_all` — skipped because no Redis available
- These are integration tests requiring a running Redis instance

## Test Infrastructure Notes

| Aspect | Current | Recommendation |
|--------|---------|---------------|
| Database | SQLite `./test.db` (shared file) | Use `:memory:` for test isolation |
| DB fixtures | `setup_db` autouse per test | Good — clean state per test |
| Test client | `TestClient(app)` with DB override | Good pattern |
| Fixture scope | All `function` scope | Good — avoids cross-test contamination |
| Test data | UUID-based random IDs | Acceptable |
| Async mode | `Mode.STRICT` | Good — catches missing awaits |

## Frontend Build Quality

| Metric | Value |
|--------|-------|
| Pages generated | 18 static + 3 dynamic |
| Errors | 0 |
| Warnings | 0 |
| First Load JS shared | 87.5 kB |
| Framework | Next.js 14.2.35 |

## Recommendations

1. **Fix calibration tests** — provide proper mock prediction inputs to `calibrate()`
2. **Fix password hashing tests** — pin bcrypt version or mock CryptContext
3. **Set up CI pipeline** — run `pytest`, `next build`, and lint on every PR
4. **Add coverage reporting** — `pytest-cov` with minimum 80% threshold
5. **Add API integration tests** — test full request-response cycles for all 15 API routers
6. **Consider adding frontend tests** — currently 0 frontend tests exist
