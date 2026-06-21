# ForecastEngine2026 v1.0 — API Reference

## Base URL
All API endpoints are served under the prefix `/api/v1` (except health).

## Core Prediction Endpoints

### POST /api/v1/predictions
Get predictions for matches.

### GET /api/v1/predictions/rankings
Compute and return IGF rankings for all teams.

### GET /api/v1/matches/{match_id}/prediction
Get prediction for a specific match.

### GET /api/v1/predictions/full/{match_id}
Full detailed prediction with confidence, BTTS, over/under, clean sheets.

**Response fields:**
- home_win_prob / draw_prob / away_win_prob
- home_expected_goals / away_expected_goals
- confidence / confidence_level
- surprise_risk
- btts_prob (both teams to score)
- over_25_prob / under_25_prob / over_35_prob
- home_clean_sheet_prob / away_clean_sheet_prob
- top_scores (top 10 scorelines)

### GET /api/v1/predictions/betting/{match_id}
Betting-market-style probabilities.

---

## Explain Endpoint

### GET /api/v1/matches/explain?home_team_id=...&away_team_id=...&home_advantage=true
Predict and explain a match with per-signal driver breakdown.

**Response fields:**
- home_win_prob / draw_prob / away_win_prob
- home_strength / away_strength
- signal_drivers: {elo, xg_attack, xg_defense, fifa} with contribution percentages
- confidence_level

---

## Scenario Endpoint

### POST /api/v1/scenarios/simulate
Run a what-if scenario with team strength modifiers.

**Request body (ScenarioRequest):**
```json
{
  "modifications": [
    {
      "team_id": "uuid",
      "elo_modifier": 50,
      "xg_for_modifier": 0.3,
      "xg_against_modifier": -0.2
    }
  ],
  "num_scenarios": 1000
}
```

**Response:** Simulated probabilities under modified conditions.

---

## Comparison Endpoint

### GET /api/v1/comparison/teams/{team_a_id}/{team_b_id}
Side-by-side comparison of two teams.

**Response fields:**
- team_a / team_b: elo_score, fifa_rank, igf_score, group info
- head_to_head_prediction (if same group)

---

## Ranking Endpoints

### GET /api/v1/rankings/elo
Elo ratings with pagination.

### GET /api/v1/rankings/fifa
FIFA rankings with pagination.

### GET /api/v1/rankings/igf
Integrated Grading Formula scores.

### GET /api/v1/rankings/power-ranking
Power rankings: title contenders, SF/QF candidates, early exits.

---

## Simulation Endpoints

### GET /api/v1/simulations
List simulations with pagination.

### POST /api/v1/simulations
Create a new simulation.

### POST /api/v1/simulations/{sim_id}/run
Execute a simulation.

### GET /api/v1/simulations/{sim_id}
Get simulation results.

### GET /api/v1/simulations/{sim_id}/probabilities
Get per-team and per-group probabilities.

---

## Dashboard Endpoint

### GET /api/v1/dashboard
Main dashboard data: totals, top teams, simulation probs, predictions, standings.

---

## Export Endpoints

### GET /api/v1/export/team/{team_id}
### GET /api/v1/export/match/{match_id}
### GET /api/v1/export/simulation/{sim_id}
### GET /api/v1/export/group/{group_id}
### GET /api/v1/export/rankings
### GET /api/v1/export/matches/csv
### GET /api/v1/export/simulations/csv

---

## Calibration Endpoints

### POST /api/v1/calibration/run
Run calibration against historical WC data.

### POST /api/v1/calibration/benchmark
Benchmark all models.

### GET /api/v1/calibration/results
Get last calibration report.

### POST /api/v1/calibration/apply
Apply calibration adjustments.

### GET /api/v1/calibration/adjustments
Get active adjustments.

### POST /api/v1/calibration/refinement/run
Run full calibration refinement.

### GET /api/v1/calibration/refinement/results
Get refinement results.

---

## Health Endpoints

### GET /health
Project status.

### GET /health/database
Database connection status.

### GET /health/redis
Redis connection status.

### GET /health/system
System information (Python, platform, CPU).

### GET /metrics
Prometheus metrics.

---

## Standard Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| skip | int | Pagination offset (default 0) |
| limit | int | Pagination limit (default 20, max 100) |
| stage | str | Filter by tournament stage |

## Rate Limiting

| Endpoint | Limit |
|----------|-------|
| GET /predictions | 10/min |
| POST /simulations | 5/min |
| POST /simulations/{id}/run | 5/min |
| POST /scenarios/simulate | 5/min |
