# Stress Root Cause Analysis

## Objective
Decompose the stress_test std = 0.090 into per-variable contributions
to identify the root causes of prediction instability.

## Methodology
Each variable is perturbed independently (200 random perturbations each)
while keeping other variables fixed. The resulting std of home_win probability
measures that variable's contribution to total stress.

## Results

| Variable         | Perturbation % | Home Win Std | % of Total Std |
|------------------|----------------|-------------|----------------|
| elo              | 15%           | 0.0355      | 52.1         % |
| xg_for           | 20%           | 0.0170      | 24.9         % |
| xg_against       | 20%           | 0.0075      | 11.0         % |
| fifa_rank        | 20%           | 0.0000      | 0.0          % |
| home_advantage   | 50%           | 0.0082      | 12.0         % |

**Full Stress Test**: std = 0.0922, sensitivity = 19.45%

## Root Cause Analysis

### 1. Elo (52% of explained variance)
- **Primary source of instability**
- ±15% Elo perturbation → 0.035 std in home win probability
- Elo's high weight (0.40) amplifies any Elo estimation noise
- **Mitigation**: Reduce Elo weight, add Elo smoothing, or bound Elo changes

### 2. xG For (25% of explained variance)
- Second largest contributor
- Historical xG data is estimated (avg goals), adding noise
- **Mitigation**: Improve xG estimation for pre-2026 matches

### 3. xG Against (11% of explained variance)
- Third contributor
- Lower impact than xG For

### 4. FIFA Rank — effectively zero contribution
- Clamping in normalization absorbs rank perturbations
- Not a source of instability, but also not a useful signal

### 5. Home Advantage (12% of explained variance)
- Minor contribution (0.008 std)
- Boolean nature limits its impact

## Why Stress Std = 0.09?
The total stress std (0.09) is larger than the sum of individual components
because multiple variables are perturbed simultaneously in the full stress test,
creating a compounding effect.

**The primary driver is Elo** → reducing Elo sensitivity is the single highest-impact
improvement for robustness.

## Recommendations
1. **Reduce Elo weight** from 0.40 to 0.30-0.35
2. **Add Elo smoothing/decay** to prevent large Elo swings
3. **Improve xG estimation** for historical matches to reduce noise
4. **Re-evaluate FIFA rank normalization** (not a robustness issue but a signal quality issue)
