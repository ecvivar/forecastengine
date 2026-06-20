# Sensitivity Analysis Report

**Baseline:** {'elo': 1850, 'fifa': 5, 'xg_for': 2.0, 'xg_against': 1.0} vs {'elo': 1600, 'fifa': 30, 'xg_for': 1.3, 'xg_against': 1.5}
**Baseline Result:** home=54.15%, draw=22.02%, away=23.82%, xG=(1.8, 1.625)

## 1. Elo Sensitivity

| Elo Delta | Home Win % | Draw % | Away Win % | Home xG | Away xG |
|-----------|-----------|--------|-----------|--------|--------|
| 0 | 54.15% | 22.02% | 23.82% | 1.8 | 1.625 |
| 50 | 54.45% | 21.73% | 23.82% | 1.8 | 1.625 |
| 100 | 54.67% | 21.51% | 23.82% | 1.8 | 1.625 |
| 200 | 54.97% | 21.21% | 23.82% | 1.8 | 1.625 |
| 300 | 55.14% | 21.04% | 23.82% | 1.8 | 1.625 |

**Observation:** Elo +300 changes home win by +0.99pp. The Bayesian prior (reduced to 0.5) limits Elo's influence on match-level predictions.

## 2. xG Attack Sensitivity

| xG For Change | Home Win % | Draw % | Away Win % | Home xG | Away xG |
|--------------|-----------|--------|-----------|--------|--------|
| +0% | 54.15% | 22.02% | 23.82% | 1.8 | 1.625 |
| +10% | 56.77% | 21.53% | 21.7% | 1.98 | 1.625 |
| +20% | 59.28% | 20.98% | 19.74% | 2.16 | 1.625 |
| +30% | 61.67% | 20.4% | 17.93% | 2.34 | 1.625 |
| +50% | 66.09% | 19.17% | 14.75% | 2.7 | 1.625 |

**Observation:** xG attack +50% changes home win by +11.94pp. xG directly influences Poisson lambdas, making it the most sensitive single parameter for match prediction.

## 3. xG Defense Sensitivity

| xG Against Change | Home Win % | Draw % | Away Win % | Home xG | Away xG |
|-----------------|-----------|--------|-----------|--------|--------|
| 0% | 54.15% | 22.02% | 23.82% | 1.8 | 1.625 |
| -10% | 51.78% | 21.74% | 26.48% | 1.8 | 1.8056 |
| -20% | 49.04% | 21.27% | 29.69% | 1.8 | 2.0313 |
| -30% | 45.87% | 20.53% | 33.6% | 1.8 | 2.3214 |

**Observation:** xG defense -30% (worse defense) changes home win by -8.28pp. Defense deterioration strongly benefits the away team's expected goals.

## 4. FIFA Rank Sensitivity

| FIFA Rank | Home Win % | Draw % | Away Win % | Home xG | Away xG |
|----------|-----------|--------|-----------|--------|--------|
| 5 | 54.15% | 22.02% | 23.82% | 1.8 | 1.625 |
| 15 | 54.15% | 22.02% | 23.82% | 1.8 | 1.625 |
| 30 | 54.15% | 22.02% | 23.82% | 1.8 | 1.625 |
| 60 | 54.15% | 22.02% | 23.82% | 1.8 | 1.625 |

**Observation:** FIFA rank has zero effect on `predict_full` (match-level prediction). It only contributes to `overall_strength`, which is used by the Monte Carlo engine.

## 5. Parameter Sensitivity (HA, Prior, DC)

| Parameter | Home Win % | Draw % | Away Win % | Home xG | Away xG |
|----------|-----------|--------|-----------|--------|--------|
| HA=0.0 | 52.15% | 22.35% | 25.51% | 1.6667 | 1.625 |
| HA=0.16 | 56.1% | 21.66% | 22.23% | 1.9333 | 1.625 |
| Prior=0.0 | 43.04% | 21.22% | 35.73% | 1.8 | 1.625 |
| Prior=2.0 | 65.27% | 22.82% | 11.91% | 1.8 | 1.625 |
| DC=0.0 | 53.72% | 22.85% | 23.43% | 1.8 | 1.625 |
| Neutral | 52.15% | 22.35% | 25.51% | 1.6667 | 1.625 |

**Key Findings:**
- **Bayesian prior** (0->2.0) shifts home win by +22.23pp — the most impactful parameter
- **Home Advantage** (0->0.16) shifts home win by +3.95pp
- **Dixon-Coles** has minimal effect (~0.4-0.8pp) on win probabilities
- **Neutral venue** reduces home win by -2.00pp (equivalent to HA=0)
