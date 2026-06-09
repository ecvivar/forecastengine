# Observability Report

**Date:** 2026-06-09
**Scope:** Logging, metrics, monitoring, alerting infrastructure

---

## Logging

| Capability | Status | Details |
|------------|--------|---------|
| Structured logging | ✅ | Custom `JSONFormatter` outputs JSON with timestamp, level, logger, message |
| Request ID tracking | ✅ | UUID4 per request via `RequestLogMiddleware`, propagated to all log lines |
| HTTP request logging | ✅ | Method, path, status, duration, user-agent, client IP logged per request |
| Log levels | ✅ | Configurable via `LOG_LEVEL` env var |
| Error logging | ✅ | Exception details captured with stack traces in structured format |
| Log rotation | ❌ | No log file rotation configured |
| Log shipping | ❌ | No remote log aggregation (ELK, Datadog, etc.) |
| Async logging | ❌ | All logging is synchronous |

### Issue O1: No log rotation (Medium)
- Logs go to stdout only (Uvicorn) — no file-based rotation or retention policy
- In production with systemd/journald this is acceptable, but if deploying in containers, ensure stdout capture is configured

### Issue O2: No log aggregation (Low)
- No ELK, Loki, Datadog, or CloudWatch integration
- Debugging across multiple instances would require container log aggregation

## Metrics

| Capability | Status | Details |
|------------|--------|---------|
| Request count | ✅ | In-memory counter via `MetricsMiddleware` |
| Request duration | ✅ | Tracked in milliseconds |
| Active requests | ✅ | Gauge |
| Cache hit rate | ✅ | Hits/misses tracked by `RedisCacheService` |
| Simulation durations | ✅ | Tracked by `MetricsMiddleware` |
| DB query durations | ✅ | Tracked by `MetricsMiddleware` |
| Prometheus endpoint | ✅ | `/metrics` endpoint returns Prometheus text format |
| Thread safety | ✅ | Uses `threading.Lock` |
| Metric persistence | ❌ | In-memory only — lost on restart |
| Metric export/push | ❌ | No push to Prometheus/Grafana/CloudWatch |

### Issue O3: Metrics in-memory only (Medium)
- All metrics reset on server restart
- No historical metric data
- Cannot detect trends or set alerts on metric thresholds

## Monitoring

| Capability | Status |
|------------|--------|
| Health endpoint | ✅ `/health` returns DB status, Redis status, system info |
| Uptime tracking | ✅ Included in health response |
| APM (Sentry/OpenTelemetry) | ❌ Not configured |
| Synthetic monitoring | ❌ No heartbeat/uptime check service |
| Alerting | ❌ No alert rules configured |
| Dashboard | ❌ No Grafana or similar dashboard |

### Issue O4: No APM (High)
- No Sentry, OpenTelemetry, or Datadog APM integration
- Cannot trace slow requests across middleware/DB/cache layers
- Error tracking requires log scraping only
- **Recommendation:** Add Sentry for error tracking + basic performance monitoring

## Recommendations

1. **Add Sentry** (`sentry-sdk`) for error tracking and basic APM — 30min integration
2. **Add log rotation** — configure `logging.handlers.RotatingFileHandler` for file-based logging
3. **Export metrics** — add Prometheus push gateway or serve `/metrics` on a separate port
4. **Add health check monitoring** — configure external uptime monitoring (e.g., Pingdom, HealthChecks.io)
5. **Add structured error reporting** — all 500 errors should automatically create an alert
6. **Fix request_id propagation** — ensure request_id flows through background tasks and engine operations
