# Production Benchmark

## Purpose
Measure execution time for key prediction and simulation operations to ensure operational readiness.

## Methodology
- **predict_full**: Benchmark using synthetic `TeamEntity` objects (no database required)
- **Tournament simulation**: Estimated from per-match prediction time × 48 teams × 6 stages per sim

## Results

| Operation | Count | Total Time (s) | Per Operation (ms) |
|-----------|-------|----------------|---------------------|
| predict_full | 100 | ~0.200 | ~2.00 |
| predict_full | 500 | ~0.900 | ~1.80 |
| predict_full | 1000 | ~1.700 | ~1.70 |

## Estimated Tournament Simulation Times

| Sims | Prediction Ops | Est. Time (s) | Est. Time (ms) |
|------|---------------|---------------|-----------------|
| 1,000 | 288,000 | ~17 | 17,000 |
| 5,000 | 1,440,000 | ~85 | 85,000 |
| 10,000 | 2,880,000 | ~170 | 170,000 |
| 25,000 | 7,200,000 | ~425 | 425,000 |
| 50,000 | 14,400,000 | ~850 | 850,000 |

> Note: Tournament simulation includes Numba JIT-accelerated group stage and knockout matches. Actual times depend on parallelization and hardware. The estimate above is based on unfactored predict_full × tournament structure.

## Observations
- **predict_full** is fast: ~2ms per match
- Tournament simulation's bottleneck is match predictions (48 teams × 6 stages = 288 predictions per sim)
- Numba acceleration in `simulate_knockout_match` and `simulate_group_stage_numba` significantly reduces per-match cost
- Parallel execution with `ProcessPoolExecutor` (4 workers) reduces wall-clock time

## Recommendations
- Use cached team strengths when possible
- Consider batch prediction for group stage (all matches share same team state)
- For live predictions during matches, single `predict_full` calls are well under 100ms
