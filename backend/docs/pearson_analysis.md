# Pearson Analysis

**Known values from Sprint 8.5 (3,000 sims, 48 teams):**

| Stage | Pearson | Spearman |
|-------|---------|----------|
| champion | 0.909 | 0.956 |
| final | 0.928 | 0.949 |
| semi | 0.941 | 0.940 |
| quarter | 0.954 | 0.938 |
| r16 | 0.961 | 0.944 |

**Mean Pearson:** 0.938

**Strength range:** 1.2820 - 1.5786 (std=0.1048)

## Analysis
- Strength->champion probability is sigmoid-like (non-linear)
- Spearman is consistently higher than Pearson - rank-based evaluation is more appropriate
- Pearson decays at champion stage because of ceiling/floor effects
- **Root cause:** top teams compressed near ceiling, bottom teams near floor
- Using log(strength) does NOT improve Pearson (0.909 vs 0.912) - confirms saturation

## Remedy
1. Use Spearman for primary evaluation (Pearson assumes linearity)
2. Increase ensemble diversity to spread probabilities
3. Add mid-tier differentiation (wider strength gradient for teams 5-20)