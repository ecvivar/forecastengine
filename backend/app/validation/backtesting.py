"""
Sprint 3 — FASE 2: Historical Backtesting Engine.

Evaluates match prediction engine against World Cup 2014, 2018, 2022.
Builds per-team entities from historical data, simulates matches, 
and compares predictions against real outcomes.

Does NOT modify Monte Carlo Numba pipeline.
"""

import logging
import random
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations

import numpy as np

from app.data.historical_matches import ALL_HISTORICAL_MATCHES
from app.domain.calibration import HistoricalMatchData
from app.domain.entities import PredictionConfig, TeamEntity
from app.engine.match_prediction import MatchPredictionEngine
from app.validation.calibration_metrics import CalibrationMetrics

logger = logging.getLogger(__name__)


@dataclass
class TournamentBacktestResult:
    predicted_champion: str
    real_champion: str
    champion_probability: float
    top4_accuracy: float
    finalist_accuracy: float
    avg_brier: float
    avg_log_loss: float
    avg_rps: float
    ece: float
    match_count: int
    tournament: str = ""
    n_simulations: int = 0


class BacktestingEngine:
    """Evaluate prediction engine against historical World Cups."""

    def __init__(self, config: PredictionConfig | None = None):
        self.config = config or PredictionConfig()
        self.engine = MatchPredictionEngine(config=self.config)
        self.metrics = CalibrationMetrics()

    # ── Build TeamEntity from historical data ──

    @staticmethod
    def _extract_team_data(matches: list[HistoricalMatchData]) -> dict[str, dict]:
        """
        Build per-team stats from historical matches.
        
        Returns: {team_name: {
            "elo": int (first match elo),
            "goals_for": [int], "goals_against": [int], "matches": [...]
        }}
        """
        teams: dict[str, dict] = {}
        for m in matches:
            for side in ("home", "away"):
                name = getattr(m, f"{side}_team")
                elo = getattr(m, f"{side}_elo")
                if side == "home":
                    gf, ga = m.home_goals, m.away_goals
                else:
                    gf, ga = m.away_goals, m.home_goals

                if name not in teams:
                    teams[name] = {
                        "elo": elo,
                        "goals_for": [],
                        "goals_against": [],
                        "match_refs": [],
                        "confederation": getattr(m, f"{side}_confederation", ""),
                    }
                teams[name]["goals_for"].append(gf)
                teams[name]["goals_against"].append(ga)
                teams[name]["match_refs"].append(m)
        return teams

    def _build_team_entity(
        self, name: str, data: dict
    ) -> TeamEntity:
        """Create TeamEntity from extracted historical data."""
        avg_gf = float(np.mean(data["goals_for"])) if data["goals_for"] else 1.0
        avg_ga = float(np.mean(data["goals_against"])) if data["goals_against"] else 1.5
        elo = data["elo"]
        # Estimate FIFA rank from Elo (1500≈100, 2000≈1)
        est_rank = max(1, min(100, int(100 * (1 - (elo - 1300) / 800))))

        return TeamEntity(
            id=uuid.uuid4(),
            name=name,
            elo_score=elo,
            fifa_rank=est_rank,
            xg_for=round(avg_gf, 4),
            xg_against=round(avg_ga, 4),
        )

    # ── Simulate 32-team tournament (2014/2018/2022 format) ──

    @staticmethod
    def _get_tournament_groups_and_bracket(tournament: str):
        """
        Return group assignments and bracket structure for 32-team World Cups.
        Groups: hardcoded to actual 2014/2018/2022 group composition.
        Bracket: standard 32-team → R16 → QF → SF → Final.
        """
        groups_2014 = {
            "A": ["Brazil", "Croatia", "Mexico", "Cameroon"],
            "B": ["Spain", "Netherlands", "Chile", "Australia"],
            "C": ["Colombia", "Greece", "Ivory Coast", "Japan"],
            "D": ["Uruguay", "Costa Rica", "England", "Italy"],
            "E": ["Switzerland", "Ecuador", "France", "Honduras"],
            "F": ["Argentina", "Bosnia and Herzegovina", "Iran", "Nigeria"],
            "G": ["Germany", "Portugal", "Ghana", "USA"],
            "H": ["Belgium", "Algeria", "Russia", "South Korea"],
        }
        groups_2018 = {
            "A": ["Russia", "Saudi Arabia", "Egypt", "Uruguay"],
            "B": ["Portugal", "Spain", "Morocco", "Iran"],
            "C": ["France", "Australia", "Peru", "Denmark"],
            "D": ["Argentina", "Iceland", "Croatia", "Nigeria"],
            "E": ["Brazil", "Switzerland", "Costa Rica", "Serbia"],
            "F": ["Germany", "Mexico", "Sweden", "South Korea"],
            "G": ["Belgium", "Panama", "Tunisia", "England"],
            "H": ["Poland", "Senegal", "Colombia", "Japan"],
        }
        groups_2022 = {
            "A": ["Qatar", "Ecuador", "Senegal", "Netherlands"],
            "B": ["England", "Iran", "USA", "Wales"],
            "C": ["Argentina", "Saudi Arabia", "Mexico", "Poland"],
            "D": ["France", "Australia", "Denmark", "Tunisia"],
            "E": ["Spain", "Costa Rica", "Germany", "Japan"],
            "F": ["Belgium", "Canada", "Morocco", "Croatia"],
            "G": ["Brazil", "Serbia", "Switzerland", "Cameroon"],
            "H": ["Portugal", "Ghana", "Uruguay", "South Korea"],
        }
        groups = {"2014": groups_2014, "2018": groups_2018, "2022": groups_2022}
        # Winner pairings for R16 (standard 32-team bracket)
        bracket_template = [
            ("1A", "2B"), ("1C", "2D"), ("1E", "2F"), ("1G", "2H"),
            ("1B", "2A"), ("1D", "2C"), ("1F", "2E"), ("1H", "2G"),
        ]
        return groups.get(tournament, groups_2022), bracket_template

    def simulate_tournament(
        self,
        matches: list[HistoricalMatchData],
        tournament: str,
        n_simulations: int = 1000,
    ) -> TournamentBacktestResult:
        """
        Simulate a complete 32-team World Cup tournament using the hybrid model.
        
        Step 1: Build TeamEntities from historical data.
        Step 2: Run match-level predictions.
        Step 3: Run full tournament simulation for champion probability.
        Step 4: Compute calibration metrics.
        """
        team_data = self._extract_team_data(matches)
        team_entities = {name: self._build_team_entity(name, d) for name, d in team_data.items()}
        group_map, bracket_tmpl = self._get_tournament_groups_and_bracket(tournament)

        # ── Match-level validation ──
        probs_list = []
        outcomes_list = []
        outcome_map = {"home": 0, "draw": 1, "away": 2}

        for m in matches:
            home_ent = team_entities.get(m.home_team)
            away_ent = team_entities.get(m.away_team)
            if not home_ent or not away_ent:
                continue
            r = self.engine.predict_full(home_ent, away_ent, home_advantage=True)
            probs_list.append([r.home_win_prob, r.draw_prob, r.away_win_prob])

            # Determine actual outcome
            if m.home_goals > m.away_goals:
                actual = [1, 0, 0]
            elif m.home_goals == m.away_goals:
                actual = [0, 1, 0]
            else:
                actual = [0, 0, 1]
            outcomes_list.append(actual)

        probs_arr = np.array(probs_list)
        outcomes_arr = np.array(outcomes_list)

        avg_brier = self.metrics.brier_score(probs_arr, outcomes_arr)
        avg_log_loss = self.metrics.log_loss(probs_arr, outcomes_arr)
        avg_rps = self.metrics.ranked_probability_score(probs_arr, outcomes_arr)
        ece, _ = self.metrics.expected_calibration_error(probs_arr, outcomes_arr)

        # ── Full tournament simulation (champion probability) ──
        champion_counts: dict[str, int] = defaultdict(int)
        real_champion = self._find_real_champion(matches, tournament)

        for _ in range(n_simulations):
            winner = self._simulate_single_tournament(
                team_entities, group_map, bracket_tmpl, matches
            )
            if winner:
                champion_counts[winner] += 1

        total_sim = sum(champion_counts.values()) or 1
        predicted_champion = max(champion_counts, key=champion_counts.get) if champion_counts else ""
        champion_prob = round(champion_counts.get(predicted_champion, 0) / total_sim * 100, 2)

        # Top 4 / Finalist accuracy
        predicted_top4 = set(
            sorted(champion_counts, key=champion_counts.get, reverse=True)[:4]
        )
        predicted_top2 = set(
            sorted(champion_counts, key=champion_counts.get, reverse=True)[:2]
        )

        real_top4 = self._find_real_top4(matches)
        real_top2 = self._find_real_top2(matches)

        top4_accuracy = len(predicted_top4 & real_top4) / 4.0 if real_top4 else 0.0
        finalist_accuracy = len(predicted_top2 & real_top2) / 2.0 if len(real_top2) == 2 else 0.0

        return TournamentBacktestResult(
            predicted_champion=predicted_champion,
            real_champion=real_champion,
            champion_probability=champion_prob,
            top4_accuracy=round(top4_accuracy, 4),
            finalist_accuracy=round(finalist_accuracy, 4),
            avg_brier=round(avg_brier, 6),
            avg_log_loss=round(avg_log_loss, 6),
            avg_rps=round(avg_rps, 6),
            ece=round(ece, 6),
            match_count=len([m for m in matches]),
            tournament=tournament,
            n_simulations=n_simulations,
        )

    def _simulate_single_tournament(
        self,
        team_entities: dict[str, TeamEntity],
        group_map: dict[str, list[str]],
        bracket_tmpl: list[tuple[str, str]],
        matches: list[HistoricalMatchData],
    ) -> str | None:
        """
        Simulate one complete 32-team tournament using predict_full.
        Returns champion name or None.
        """
        # Group stage
        group_results: dict[str, list[tuple[int, int, int]]] = defaultdict(list)
        # group_results[group] = [(points, gd, gf)] for each team in group order

        for grp_name, team_names in group_map.items():
            for a, b in combinations(team_names, 2):
                ha = team_entities.get(a)
                hb = team_entities.get(b)
                if not ha or not hb:
                    continue
                # Home/away is arbitrary for group stage
                r1 = self.engine.predict_full(ha, hb, home_advantage=False)
                # Simulate actual result from probabilities
                outcome = random.random()
                if outcome < r1.home_win_prob:
                    pts_a, pts_b = 3, 0
                    gf_a, gf_b = self._sample_goals(r1.home_expected_goals), self._sample_goals(r1.away_expected_goals)
                elif outcome < r1.home_win_prob + r1.draw_prob:
                    pts_a, pts_b = 1, 1
                    gf_a = gf_b = self._sample_goals((r1.home_expected_goals + r1.away_expected_goals) / 2)
                else:
                    pts_a, pts_b = 0, 3
                    gf_a, gf_b = self._sample_goals(r1.away_expected_goals), self._sample_goals(r1.home_expected_goals)
                group_results[grp_name].append((a, pts_a, gf_a - gf_b, gf_a))
                group_results[grp_name].append((b, pts_b, gf_b - gf_a, gf_b))

        # Rank teams within group
        group_rankings: dict[str, list[str]] = {}
        for grp_name, team_names in group_map.items():
            standings: dict[str, list] = defaultdict(lambda: [0, 0, 0])
            for tname, pts, gd, gf in group_results[grp_name]:
                standings[tname][0] += pts
                standings[tname][1] += gd
                standings[tname][2] += gf
            sorted_teams = sorted(
                team_names,
                key=lambda t: (standings[t][0], standings[t][1], standings[t][2]),
                reverse=True,
            )
            group_rankings[grp_name] = sorted_teams

        # Build knockout bracket
        bracket_map = {}
        for grp_name, ranking in group_rankings.items():
            bracket_map[f"1{grp_name}"] = ranking[0]
            bracket_map[f"2{grp_name}"] = ranking[1]

        # R16
        r16_winners = []
        for pair_a, pair_b in bracket_tmpl:
            ta = bracket_map.get(pair_a)
            tb = bracket_map.get(pair_b)
            if not ta or not tb:
                continue
            winner = self._simulate_knockout(team_entities, ta, tb)
            if winner:
                r16_winners.append(winner)

        # QF
        qf_winners = []
        for i in range(0, len(r16_winners), 2):
            if i + 1 < len(r16_winners):
                w = self._simulate_knockout(team_entities, r16_winners[i], r16_winners[i + 1])
                if w:
                    qf_winners.append(w)

        # SF
        sf_winners = []
        for i in range(0, len(qf_winners), 2):
            if i + 1 < len(qf_winners):
                w = self._simulate_knockout(team_entities, qf_winners[i], qf_winners[i + 1])
                if w:
                    sf_winners.append(w)

        # Final
        if len(sf_winners) >= 2:
            return self._simulate_knockout(team_entities, sf_winners[0], sf_winners[1])

        return None

    def _simulate_knockout(
        self, entities: dict[str, TeamEntity], a: str, b: str
    ) -> str | None:
        """Simulate a single knockout match. Returns winner name or None."""
        ea = entities.get(a)
        eb = entities.get(b)
        if not ea or not eb:
            return None
        r = self.engine.predict_full(ea, eb, home_advantage=False)
        outcome = random.random()
        if outcome < r.home_win_prob:
            return a
        elif outcome < r.home_win_prob + r.draw_prob:
            # Extra time / penalties: pick randomly
            return a if random.random() < 0.5 else b
        else:
            return b

    @staticmethod
    def _sample_goals(lambda_: float) -> int:
        return int(np.random.poisson(max(0.1, lambda_)))

    @staticmethod
    def _find_real_champion(
        matches: list[HistoricalMatchData], tournament: str
    ) -> str:
        """Find the actual champion from historical match data."""
        finals = [m for m in matches if m.stage == "final"]
        if finals:
            f = finals[0]
            return f.home_team if f.home_goals > f.away_goals else f.away_team
        return {"2014": "Germany", "2018": "France", "2022": "Argentina"}.get(tournament, "")

    @staticmethod
    def _find_real_top4(matches: list[HistoricalMatchData]) -> set[str]:
        """Find actual semi-finalists (top 4)."""
        semis = [m for m in matches if m.stage == "semi_final"]
        top4 = set()
        for s in semis:
            top4.add(s.home_team)
            top4.add(s.away_team)
        if not top4:
            return {"Germany", "Argentina", "Netherlands", "Brazil"}
        return top4

    @staticmethod
    def _find_real_top2(matches: list[HistoricalMatchData]) -> set[str]:
        """Find actual finalists (top 2)."""
        finals = [m for m in matches if m.stage == "final"]
        if finals:
            f = finals[0]
            return {f.home_team, f.away_team}
        return set()

    def run_all(
        self, n_simulations: int = 1000
    ) -> list[TournamentBacktestResult]:
        """Run backtest for all three tournaments."""
        results = []
        for tournament in ("2014", "2018", "2022"):
            matches = [m for m in ALL_HISTORICAL_MATCHES if m.tournament == tournament]
            if not matches:
                logger.warning(f"No matches found for {tournament}, skipping")
                continue
            logger.info(f"Backtesting {tournament}: {len(matches)} matches")
            result = self.simulate_tournament(matches, tournament, n_simulations)
            results.append(result)
        return results
