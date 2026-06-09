# Data Quality Report

**Date:** 2026-06-09
**Scope:** Historical match data (192 WC matches 2014-2022), team data, ranking data

---

## Historical Matches Dataset

| Attribute | Value |
|-----------|-------|
| Total matches | 192 (2014: 64, 2018: 64, 2022: 64) |
| Columns | 14 (tournament, stage, home_team, away_team, home_goals, away_goals, home_elo, away_elo, home_igf, away_igf, home_penalties, away_penalties, home_confederation, away_confederation) |
| Null values | `home_penalties`/`away_penalties` = None for 179 non-shootout matches (legitimate) |
| Missing values | 0 missing in all other columns |
| Empty confederations | 0 |

### Issues Found

#### Issue D1: No schema-level validation (Medium)
- `HistoricalMatchData` is a `@dataclass` with no Pydantic constraints
- No range checks: negative goals, Elo outside 0-2500, IGF outside 0-100 are all accepted
- **Impact:** Silent data corruption possible if data source changes

#### Issue D2: No date normalization (Low)
- Matches stored by tournament year only, no exact kickoff datetime
- Time-dependent features (form, momentum) cannot be computed reliably
- **Impact:** Relegates the model to tournament-level features only

#### Issue D3: Penalty data is binary only (Low)
- Only `home_penalties`/`away_penalties` (int or None) — no shootout detail
- Penalty outcome is inferrable but not explicit
- **Impact:** Minor — penalty probability modeling limited

#### Issue D4: Team names not validated (Low)
- `CONFEDERATIONS` dict lookup uses team name as key; unknown names return `""` silently
- No assert/log when a team name is missing from the lookup
- **Impact:** Could produce silently empty confederation values

## Data Freshness

| Dataset | Last Updated | Coverage |
|---------|-------------|----------|
| Historical matches | Hardcoded in source | 192 matches, 2014-2022 |
| Confederation mapping | Hardcoded | 48 teams across 6 confederations |
| Elo ratings | Computed from match history | Updated each tournament cycle |
| IGF scores | Computed from component scores | Last computed at build/deploy |

### Issue D5: Static historical data (High)
- All historical match data is hardcoded as a Python list in `historical_matches.py`
- Not pulled from a database or live API
- No mechanism to add 2026 matches without a code deploy
- **Impact:** Operational — requires code change to update data

## Recommendations

1. **Add Pydantic validation** to `HistoricalMatchData` with range checks for goals (>=0), Elo (0-2500), IGF (0-100)
2. **Migrate historical data to database** with a `historical_matches` table and seed migration
3. **Add confederation lookup warning** — log when a team name is not found
4. **Consider adding exact dates** to enable form/momentum features
5. **Implement data freshness monitoring** — track when data was last updated in a metadata table
