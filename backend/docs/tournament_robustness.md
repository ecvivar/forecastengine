# Tournament Robustness Analysis

## Objective
Validate that 10,000 simulations are sufficient for stable tournament-level
probability estimates by comparing convergence at 100, 500, 1000, 5000, 10000,
and 50000 simulations.

## Methodology
Using the binomial approximation (champion probability follows a Bernoulli process),
we compute the theoretical variance, standard deviation, and 90% CI width for
a team with true champion probability p = 12% (typical for the top team).

## Results

| N Sims | Theoretical Variance | Theoretical Std | CI 90% Width | CI 90% |
|--------|---------------------|----------------|--------------|--------|
| 100 | 0.00105600 | 0.032496 | 0.1069 | [0.0665, 0.1735] |
| 500 | 0.00021120 | 0.014533 | 0.0478 | [0.0961, 0.1439] |
| 1000 | 0.00010560 | 0.010276 | 0.0338 | [0.1031, 0.1369] |
| 5000 | 0.00002112 | 0.004596 | 0.0151 | [0.1124, 0.1276] |
| 10000 | 0.00001056 | 0.003250 | 0.0107 | [0.1147, 0.1253] |
| 50000 | 0.00000211 | 0.001453 | 0.0048 | [0.1176, 0.1224] |

## Convergence Analysis

### CI Width vs. N Simulations
- **100 sims**: CI width ~0.107 (e.g., champion prob = 12% ± 5.4%)
- **1,000 sims**: CI width ~0.034 (12% ± 1.7%)
- **10,000 sims**: CI width ~0.011 (12% ± 0.5%)
- **50,000 sims**: CI width ~0.005 (12% ± 0.2%)

### Diminishing Returns
- Going from 100 → 1,000 sims: CI width reduces by 3.2×
- Going from 1,000 → 10,000 sims: CI width reduces by 3.1×
- Going from 10,000 → 50,000 sims: CI width reduces by 2.2×

The marginal benefit decreases as √(n), following the Central Limit Theorem.

## Conclusions

### Is 10k enough? YES
- At 10,000 simulations, 90% CI width = ±0.5% for the top team
- This is sufficient for:
  - **Comparative analysis**: Ranking teams by champion probability
  - **Decision support**: Identifying favorites vs. long shots
  - **Confidence reporting**: CI width is <1% for practical purposes

### When to use more simulations
- **50,000+**: When sub-percentage precision matters (e.g., betting odds)
- **100,000+**: Academic research requiring extreme precision
- **500+**: Exploratory/sandbox analysis (fast feedback)

### Confidence Interval Interpretation
The 90% CI means: "If we ran the tournament 100 times (each with N sims),
the true probability would fall within the CI in ~90 of those runs."

For n=10,000: CI = [11.7%, 12.3%] — we are 90% confident the true champion
probability is within 0.3% of our estimate.

## Recommendations
1. **Keep 10,000 as the default** — optimal balance of precision and speed
2. **Offer 50,000 option** for critical decisions (e.g., pre-match strategy)
3. **Use 1,000 for rapid iteration** during model development
4. **Report CI with all tournament probabilities** for transparency
