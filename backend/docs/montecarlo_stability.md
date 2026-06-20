# Monte Carlo Stability Report

## Convergence Analysis

| Simulations | Time (s) | Max Delta from Prev (pp) | Mean Delta from Prev (pp) |
|------------|---------|-------------------------|-------------------------|
|    100 |    3.74 |                        — |                        — |
|    500 |    0.25 |                    6.000 |                    2.760 |
|   1000 |    0.51 |                    2.200 |                    1.050 |
|   5000 |    2.51 |                    1.840 |                    0.596 |
|  10000 |    5.21 |                    0.710 |                    0.454 |
|  50000 |   25.61 |                    0.300 |                    0.137 |

## Top 10 Champion Probabilities at Each Simulation Size

### n=100

| Rank | Team | Champion % | Finalist % | Semi % |
|------|------|-----------|----------|-------|
| 1 | Brazil | 15.0% | 19.0% | 25.0% |
| 2 | France | 9.0% | 14.0% | 26.0% |
| 3 | Germany | 9.0% | 13.0% | 24.0% |
| 4 | Spain | 8.0% | 15.0% | 23.0% |
| 5 | Italy | 7.0% | 16.0% | 19.0% |
| 6 | Croatia | 7.0% | 10.0% | 20.0% |
| 7 | England | 5.0% | 10.0% | 23.0% |
| 8 | Argentina | 4.0% | 6.0% | 12.0% |
| 9 | Belgium | 4.0% | 10.0% | 19.0% |
| 10 | Netherlands | 3.0% | 6.0% | 10.0% |

### n=500

| Rank | Team | Champion % | Finalist % | Semi % |
|------|------|-----------|----------|-------|
| 1 | France | 10.4% | 15.4% | 23.8% |
| 2 | Brazil | 9.0% | 16.6% | 27.8% |
| 3 | Argentina | 6.6% | 11.0% | 18.8% |
| 4 | Belgium | 6.2% | 11.2% | 18.6% |
| 5 | England | 6.0% | 10.6% | 18.6% |
| 6 | Spain | 5.6% | 10.2% | 18.6% |
| 7 | Germany | 5.6% | 9.8% | 19.2% |
| 8 | Croatia | 5.4% | 10.8% | 18.8% |
| 9 | Netherlands | 5.0% | 12.6% | 23.4% |
| 10 | Uruguay | 5.0% | 10.2% | 17.0% |

### n=1000

| Rank | Team | Champion % | Finalist % | Semi % |
|------|------|-----------|----------|-------|
| 1 | France | 11.0% | 16.2% | 25.3% |
| 2 | Brazil | 9.2% | 16.2% | 25.3% |
| 3 | Spain | 7.8% | 11.7% | 22.8% |
| 4 | Argentina | 7.1% | 11.5% | 19.6% |
| 5 | Portugal | 6.1% | 9.6% | 18.9% |
| 6 | Netherlands | 6.0% | 9.7% | 20.2% |
| 7 | Italy | 5.4% | 11.4% | 19.6% |
| 8 | England | 5.2% | 9.7% | 16.8% |
| 9 | Belgium | 5.0% | 10.7% | 19.1% |
| 10 | Germany | 4.9% | 10.4% | 19.6% |

### n=5000

| Rank | Team | Champion % | Finalist % | Semi % |
|------|------|-----------|----------|-------|
| 1 | Brazil | 9.18% | 14.78% | 24.34% |
| 2 | France | 9.16% | 14.84% | 24.28% |
| 3 | Spain | 7.2% | 11.6% | 22.14% |
| 4 | Argentina | 6.42% | 11.22% | 19.52% |
| 5 | Netherlands | 6.24% | 10.34% | 19.68% |
| 6 | Italy | 5.76% | 10.64% | 18.48% |
| 7 | Germany | 5.64% | 10.06% | 19.84% |
| 8 | England | 5.56% | 10.28% | 17.26% |
| 9 | Belgium | 5.34% | 10.86% | 18.78% |
| 10 | Portugal | 5.32% | 9.66% | 18.06% |

### n=10000

| Rank | Team | Champion % | Finalist % | Semi % |
|------|------|-----------|----------|-------|
| 1 | Brazil | 9.87% | 15.02% | 24.4% |
| 2 | France | 9.87% | 15.55% | 25.16% |
| 3 | Spain | 7.23% | 12.57% | 22.78% |
| 4 | Argentina | 6.8% | 11.23% | 19.4% |
| 5 | Germany | 6.13% | 10.04% | 19.54% |
| 6 | Netherlands | 5.83% | 10.38% | 19.65% |
| 7 | Italy | 5.14% | 11.0% | 19.23% |
| 8 | England | 5.05% | 8.45% | 15.39% |
| 9 | Croatia | 4.72% | 10.25% | 18.51% |
| 10 | Portugal | 4.64% | 8.55% | 17.31% |

### n=50000

| Rank | Team | Champion % | Finalist % | Semi % |
|------|------|-----------|----------|-------|
| 1 | Brazil | 9.81% | 15.21% | 24.44% |
| 2 | France | 9.67% | 15.06% | 24.44% |
| 3 | Spain | 7.16% | 12.06% | 22.64% |
| 4 | Argentina | 6.77% | 11.31% | 19.07% |
| 5 | Germany | 5.83% | 10.03% | 19.31% |
| 6 | Netherlands | 5.83% | 10.24% | 19.81% |
| 7 | England | 5.34% | 9.3% | 16.67% |
| 8 | Italy | 5.15% | 10.83% | 18.97% |
| 9 | Belgium | 4.85% | 10.46% | 18.53% |
| 10 | Portugal | 4.82% | 8.71% | 17.49% |

## Conclusions

1. **10,000 simulations** provide stable results: max delta < 0.71pp from 5,000.
2. **50,000 simulations** add marginal improvement: max delta < 0.30pp from 10,000.
3. At 100 simulations, results are unreliable (max delta of 6.0pp to 500).
4. The recommended default is **10,000 simulations** (5.2s runtime) for a good balance of accuracy and speed.
5. For production-critical decisions, **50,000 simulations** (25.6s) provides the highest confidence.
