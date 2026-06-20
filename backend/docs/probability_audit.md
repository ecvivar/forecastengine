# Probability Consistency Audit

## Methodology

For each simulation size, we verify that the sum of probabilities across all 48 teams satisfies:
- Champion probability = 100% (exactly 1 winner)
- Finalist probability = 200% (2 finalists)
- Semifinal probability = 400% (4 semifinalists)
- Quarterfinal probability = 800% (8 quarterfinalists)
- Round of 16 probability = 1600% (16 teams)
- Round of 32 probability = 3200% (32 teams)

## Results

| N Sims | Champion | Finalist | Semi | Quarter | R16 | R32 | Status |
|--------|---------|---------|------|--------|-----|-----|--------|
|    100 |  100.00% |  200.00% | 400.00% |  800.00% | 1600.00% | 3200.00% | **PASS** |
|    500 |  100.00% |  200.00% | 400.00% |  800.00% | 1600.00% | 3200.00% | **PASS** |
|   1000 |  100.00% |  200.00% | 400.00% |  800.00% | 1600.00% | 3200.00% | **PASS** |
|   5000 |  100.00% |  200.00% | 400.00% |  800.00% | 1600.00% | 3200.00% | **PASS** |
|  10000 |  100.00% |  200.00% | 400.00% |  800.00% | 1600.00% | 3200.00% | **PASS** |
|  50000 |   99.99% |  200.04% | 400.00% |  800.03% | 1599.98% | 3200.01% | **PASS** |

## Findings

- **ALL simulation sizes pass** the probability consistency audit.
- Maximum deviation observed: 0.04pp at 50,000 simulations (finalist probability = 200.04%).
- Deviations are due to floating-point rounding, not structural issues.
- The Monte Carlo engine correctly tracks all tournament stages with no double-counting or missed transitions.
