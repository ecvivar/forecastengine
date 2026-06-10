# DEPLOY-008: Cost Analysis Report

**Date:** 2026-06-10
**Stack:** Neon (PostgreSQL) · Upstash (Redis) · Vercel (Frontend) · Docker (Backend)
**Region:** US East (Ohio) — default for all services

---

## Assumptions

| Parameter | Hobby | Growth | Popular |
|-----------|-------|--------|---------|
| Daily active users | 100 | 1,000 | 10,000 |
| Requests/user/day | 20 | 30 | 50 |
| Daily requests | 2,000 | 30,000 | 500,000 |
| Peak concurrent users | 5 | 50 | 500 |
| Simulations/day | 50 | 500 | 5,000 |
| Data storage | 500 MB | 2 GB | 10 GB |
| Backend nodes | 1 | 2 | 4 |
| Monitoring | Free tier | Team tier | Team tier |

---

## Hobby — 100 users/day

### Monthly Costs

| Service | Plan | Cost | Notes |
|---------|------|------|-------|
| **Neon PostgreSQL** | Free (0.5 GB, 100h compute) | $0 | 100 compute hours/month = ~3.3h/day — sufficient for low traffic |
| **Upstash Redis** | Free (256 MB, 10,000 cmds/day) | $0 | 10k commands/day covers 2k API requests with caching |
| **Vercel Frontend** | Hobby (100 GB bandwidth) | $0 | Static JS bundles, ~50 MB per deploy |
| **Docker Host** | Railway Hobby ($5/mo) or single VPS | $5–10 | 1 CPU, 1 GB RAM, 50 GB storage |
| **Sentry** | Free (5k events/month) | $0 | Should be well under 5k at this volume |
| **Better Stack** | Free (3 uptime monitors) | $0 | Monitor health endpoints |
| **Domain** | .com (.dev, etc.) | $12/yr | |
| **Total** | | **$5–10/mo** | |
| **Annual** | | **$72–132/yr** | |

### Capacity Check

| Metric | Limit | Hobby Usage | Headroom |
|--------|-------|-------------|----------|
| Neon compute hours | 100h/mo | ~30h | 70% |
| Neon storage | 500 MB | <100 MB | >80% |
| Vercel bandwidth | 100 GB/mo | <5 GB | >95% |
| Backend CPU | 1 core | ~10% at peak | 90% |
| Backend RAM | 1 GB | ~300 MB | 70% |

**Verdict:** Free tier covers everything except hosting. Total cost: **~$8/mo**.

---

## Growth — 1,000 users/day

### Monthly Costs

| Service | Plan | Cost | Notes |
|---------|------|------|-------|
| **Neon PostgreSQL** | Launch (10 GB, 500h compute) | $19 | Pooled connections, autosuspend off |
| **Upstash Redis** | Pay-as-you-go (1 GB, 500k cmds/day) | $5 | Caching + rate limiting state |
| **Vercel Frontend** | Pro ($20/mo) | $20 | 1 TB bandwidth, team features |
| **Docker Host** | Railway Pro ($25/mo) × 2 nodes | $50 | 2 × 2 CPU, 4 GB RAM |
| **Sentry** | Team ($29/mo) | $29 | 50k events, 1 user |
| **Better Stack** | Uptime ($14/mo) | $14 | 10 monitors, 5m intervals |
| **Domain** | .com | $12/yr | |
| **Total** | | **$137/mo** | |
| **Annual** | | **$1,656/yr** | |

### Capacity Check

| Metric | Limit | Growth Usage | Headroom |
|--------|-------|-------------|----------|
| Neon compute hours | 500h/mo | ~200h | 60% |
| Neon storage | 10 GB | <2 GB | 80% |
| Vercel bandwidth | 1 TB/mo | <50 GB | 95% |
| Backend (×2) | 4 CPU, 8 GB RAM | ~30% at peak | 70% |
| Redis commands | 500k/day | <100k/day | 80% |

**Verdict:** Everything fits comfortably. Total cost: **~$140/mo**.

---

## Popular — 10,000 users/day

### Monthly Costs

| Service | Plan | Cost | Notes |
|---------|------|------|-------|
| **Neon PostgreSQL** | Scale (50 GB, 1000h compute) | $69 | Auto-scale CPU 0.5–8, pooled connections |
| **Upstash Redis** | Pro (5 GB, 5M cmds/day) | $25 | Session caching + rate limiting |
| **Vercel Frontend** | Pro ($20/mo) + Enterprise add-ons | $50 | 1 TB bandwidth, likely need more |
| **Docker Host** | Railway Scale ($75/mo) × 4 nodes | $300 | 4 × 4 CPU, 8 GB RAM |
| **Sentry** | Business ($80/mo) | $80 | 500k events |
| **Better Stack** | Uptime ($35/mo) | $35 | 50 monitors, 1m intervals |
| **CDN** | Included in Vercel | $0 | Edge caching for static assets |
| **Domain** | .com | $12/yr | |
| **Total** | | **$559/mo** | |
| **Annual** | | **$6,720/yr** | |

### Capacity Check

| Metric | Limit | Popular Usage | Headroom |
|--------|-------|-------------|----------|
| Neon compute hours | 1000h/mo | ~720h | 28% — may need more |
| Neon storage | 50 GB | <10 GB | 80% |
| Vercel bandwidth | 1 TB/mo | ~750 GB | 25% — consider Enterprise |
| Backend (×4) | 16 CPU, 32 GB RAM | ~50% at peak | 50% |
| Redis commands | 5M/day | ~2M/day | 60% |

**Potential bottlenecks at 10k users/day:**
1. **Neon compute hours** — 720h/mo usage at 10k users (24h/day × 30d) leaves only 28% headroom. May need Scale plan with 2000h ($99/mo).
2. **Vercel bandwidth** — ~750 GB/mo at 10k users with 50 requests each. Pro plan includes 1 TB. May hit overage charges (~$0.20/GB).
3. **Backend CPU** — 4 nodes × 4 CPU = 16 cores. Load test showed ~69 req/s per single worker. With 4 nodes × 2 workers each → ~550 req/s theoretical max. At peak 500 concurrent users, estimated ~200 req/s. Comfortable.

**Verdict:** At 10k users, upgrade Neon to Scale-2000h ($99/mo) and consider Vercel Enterprise for higher bandwidth. Adjusted total: **~$600/mo**.

---

## Summary

| Tier | Monthly | Annual | Best for |
|------|---------|--------|----------|
| **Hobby** | $5–10 | $72–132 | Personal project, demo, small group |
| **Growth** | ~$140 | ~$1,656 | Regional launch, moderate traffic |
| **Popular** | ~$600 | ~$7,200 | Production at scale, media event |

### Cost Per User

| Tier | Monthly Cost | Users/Mo | Cost/User/Mo |
|------|-------------|----------|------------|
| Hobby | $8 | 3,000 | **$0.0027** |
| Growth | $140 | 30,000 | **$0.0047** |
| Popular | $600 | 300,000 | **$0.0020** |

The cost efficiency improves at scale due to fixed infrastructure costs being amortized over more users.

### One-Time Setup Costs

| Item | Cost |
|------|------|
| Domain registration | $12 |
| SSL certificate (Vercel provides) | $0 |
| Neon project creation | $0 |
| CI/CD pipeline setup | ~4h dev time |

---

## Cost Optimization Opportunities

1. **Reduce Neon compute hours** — Enable Neon's autosuspend for non-production environments (saves ~$19/mo on Growth tier)
2. **Cache aggressively** — The DEPLOY-005 cache audit showed 8.3x–43.6x speedups. Better caching = less DB compute = lower Neon costs
3. **Use Upstash Redis free tier** for Growth tier — 256 MB is sufficient for cache-only workload (no session storage)
4. **Backend on spot/preemptible instances** — If using raw cloud (AWS/GCP) instead of Railway, spot instances cut compute costs ~60%
5. **Static page optimization** — All frontend pages are static prerendered (SSG). Add CDN caching with 5-minute TTL to reduce Vercel function invocations
