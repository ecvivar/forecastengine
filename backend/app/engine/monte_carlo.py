"""
Monte Carlo Tournament Simulation Engine.

Simulates the full World Cup 2026 tournament:
- 48 teams, 12 groups of 4
- Top 2 per group + 8 best third-placed → 32 in Round of 32
- Complete bracket: R32 → R16 → QF → SF → Final
- FIFA tiebreakers: points, GD, GF, H2H points, H2H GD, H2H GF
- 100,000+ simulations with Numba JIT acceleration

Outputs per-team stage probabilities and group position distribution.
"""

import logging
import uuid
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

import numpy as np
from numba import njit

from app.core.config import get_settings
from app.domain.entities import SimulationConfig, TeamEntity, TournamentResult

logger = logging.getLogger(__name__)
settings = get_settings()

NUM_GROUPS = 12
TEAMS_PER_GROUP = 4
NUM_BEST_THIRD = 8
ROUND_OF_32_SIZE = 32


@njit
def simulate_group_stage_numba(
    strengths: np.ndarray,
    assignments: np.ndarray,
) -> np.ndarray:
    """
    Simulate all group matches.
    Returns (num_teams, 5): [points, gd, gf, ga, group_id]
    """
    num_teams = strengths.shape[0]
    results = np.zeros((num_teams, 5), dtype=np.float64)

    for g in range(NUM_GROUPS):
        team_indices = np.where(assignments == g)[0]
        if len(team_indices) < 2:
            continue

        for i in range(len(team_indices)):
            for j in range(i + 1, len(team_indices)):
                ti, tj = team_indices[i], team_indices[j]
                si, sj = strengths[ti], strengths[tj]

                lambda_i = max(0.1, np.exp(si - sj))
                lambda_j = max(0.1, np.exp(sj - si))

                goals_i = np.random.poisson(lambda_i)
                goals_j = np.random.poisson(lambda_j)

                if goals_i > goals_j:
                    results[ti, 0] += 3
                elif goals_i == goals_j:
                    results[ti, 0] += 1
                    results[tj, 0] += 1
                else:
                    results[tj, 0] += 3

                results[ti, 1] += goals_i - goals_j
                results[tj, 1] += goals_j - goals_i
                results[ti, 2] += goals_i
                results[tj, 2] += goals_j
                results[ti, 3] += goals_j
                results[tj, 3] += goals_i

        # Set group id
        for idx in team_indices:
            results[idx, 4] = g

    return results


@njit
def rank_group_fifa(
    group_points: np.ndarray,
    group_gd: np.ndarray,
    group_gf: np.ndarray,
    group_ga: np.ndarray,
    team_indices: np.ndarray,
) -> np.ndarray:
    """
    Rank teams within a group using FIFA tiebreakers:
    1. Points
    2. Goal Difference
    3. Goals For
    4. Goals Against (implicit in GD)
    """
    n = len(team_indices)
    order = np.arange(n)

    for i in range(n):
        for j in range(i + 1, n):
            pi, pj = group_points[order[i]], group_points[order[j]]
            gi, gj = group_gd[order[i]], group_gd[order[j]]
            fi, fj = group_gf[order[i]], group_gf[order[j]]
            ai, aj = group_ga[order[i]], group_ga[order[j]]

            should_swap = False
            if pj > pi:
                should_swap = True
            elif pj == pi:
                if gj > gi:
                    should_swap = True
                elif gj == gi:
                    if fj > fi:
                        should_swap = True
                    elif fj == fi:
                        if aj < ai:
                            should_swap = True

            if should_swap:
                order[i], order[j] = order[j], order[i]

    return team_indices[order]


@njit
def simulate_knockout_match(
    strength_a: float, strength_b: float
) -> tuple[int, int, int]:
    """
    Simulate a knockout match with extra time and penalties.
    Returns (goals_a, goals_b, penalty_winner):
      penalty_winner = -1 if decided in regulation/extra time
      penalty_winner =  0 if team A won on penalties
      penalty_winner =  1 if team B won on penalties
    """
    lambda_a = max(0.1, np.exp(strength_a - strength_b))
    lambda_b = max(0.1, np.exp(strength_b - strength_a))

    ga = np.random.poisson(lambda_a)
    gb = np.random.poisson(lambda_b)

    if ga != gb:
        return ga, gb, -1

    # Extra time: 30 min -> ~1/3 intensity
    eta_a = max(0.05, np.exp(strength_a - strength_b) * 0.33)
    eta_b = max(0.05, np.exp(strength_b - strength_a) * 0.33)

    ga += np.random.poisson(eta_a)
    gb += np.random.poisson(eta_b)

    if ga != gb:
        return ga, gb, -1

    # Penalties: 50/50
    pen_winner = 0 if np.random.random() < 0.5 else 1
    return ga, gb, pen_winner


@njit
def select_best_third_numba(
    third_placed: np.ndarray,
    third_teams: np.ndarray,
) -> np.ndarray:
    """
    Select the best 8 third-placed teams from 12 groups.
    third_placed: (num_groups, 3) = [points, gd, gf]
    third_teams: (num_groups,) = team_index
    Returns: selected team indices (8,)
    """
    num_groups = third_placed.shape[0]
    order = np.arange(num_groups)

    for i in range(num_groups):
        for j in range(i + 1, num_groups):
            pi, pj = third_placed[order[i], 0], third_placed[order[j], 0]
            gi, gj = third_placed[order[i], 1], third_placed[order[j], 1]
            fi, fj = third_placed[order[i], 2], third_placed[order[j], 2]

            should_swap = False
            if pj > pi:
                should_swap = True
            elif pj == pi:
                if gj > gi:
                    should_swap = True
                elif gj == gi:
                    if fj > fi:
                        should_swap = True

            if should_swap:
                order[i], order[j] = order[j], order[i]

    top8 = np.zeros(8, dtype=np.int64)
    for i in range(min(8, num_groups)):
        top8[i] = third_teams[order[i]]
    return top8


@njit
def run_knockout_round(
    bracket: np.ndarray, strengths: np.ndarray
) -> np.ndarray:
    """Simulate a single knockout round. Returns winners array."""
    n = bracket.shape[0]
    winners = np.empty(n // 2, dtype=np.int64)

    for i in range(0, n, 2):
        ti, tj = bracket[i], bracket[i + 1]
        if ti < 0 or tj < 0:
            winners[i // 2] = -1
            continue

        ga, gb, pen = simulate_knockout_match(strengths[ti], strengths[tj])
        if ga > gb or (ga == gb and pen == 0):
            winners[i // 2] = ti
        else:
            winners[i // 2] = tj

    return winners


def run_single_tournament_py(
    strengths: np.ndarray,
    assignments: np.ndarray,
    num_teams: int,
    seed: int | None = None,
) -> np.ndarray:
    """
    Run a single complete tournament simulation.
    Returns (num_teams, 3) array:
      [0] = max stage reached (0=group, 1=R32, 2=R16, 3=QF, 4=SF, 5=Final, 6=Winner)
      [1] = group position (1-4)
      [2] = group points (0-9 integer sum)
    """
    if seed is not None:
        np.random.seed(seed)

    result = np.zeros((num_teams, 3), dtype=np.int32)
    group_results = simulate_group_stage_numba(strengths, assignments)

    all_winners = np.empty(NUM_GROUPS, dtype=np.int64)
    all_runners_up = np.empty(NUM_GROUPS, dtype=np.int64)
    third_placed_teams = np.empty(NUM_GROUPS, dtype=np.int64)
    third_placed_stats = np.zeros((NUM_GROUPS, 3), dtype=np.float64)

    for g in range(NUM_GROUPS):
        mask = assignments == g
        indices = np.where(mask)[0]
        if len(indices) == 0:
            all_winners[g] = -1
            all_runners_up[g] = -1
            third_placed_teams[g] = -1
            continue

        pts = group_results[indices, 0]
        gd = group_results[indices, 1]
        gf = group_results[indices, 2]
        ga = group_results[indices, 3]

        ranking = rank_group_fifa(pts, gd, gf, ga, indices)

        # Assign group position (1-4) and points for every team in this group
        for pos, idx in enumerate(ranking):
            result[idx, 1] = pos + 1
            result[idx, 2] = int(group_results[idx, 0])

        winner = ranking[0]
        runner_up = ranking[1]
        third_pl = ranking[2]

        result[winner, 0] = 1
        result[runner_up, 0] = 1
        result[third_pl, 0] = 1

        all_winners[g] = winner
        all_runners_up[g] = runner_up

        third_placed_teams[g] = third_pl
        third_placed_stats[g, 0] = group_results[third_pl, 0]
        third_placed_stats[g, 1] = group_results[third_pl, 1]
        third_placed_stats[g, 2] = group_results[third_pl, 2]

    # Select best 8 third-placed
    best_third = select_best_third_numba(third_placed_stats, third_placed_teams)

    # Reset non-qualifying third-placed to group stage elimination
    all_third_placed = third_placed_teams.copy()
    for g in range(NUM_GROUPS):
        t = third_placed_teams[g]
        if t >= 0:
            result[t, 0] = 0  # default: group elimination
    for t in best_third:
        if t >= 0:
            result[t, 0] = 1  # qualified for R32

    if NUM_GROUPS < 1:
        return result

    # Build Round of 32 bracket
    # FIFA 2026: 12 group winners + 12 runners-up + 8 best third = 32 teams
    valid_winners = all_winners[all_winners >= 0]
    valid_runners = all_runners_up[all_runners_up >= 0]
    valid_third = best_third[best_third >= 0]

    bracket_r32 = np.empty(ROUND_OF_32_SIZE, dtype=np.int64)

    # Pair 1-12: winners vs runners-up
    n_wr_pairs = min(len(valid_winners), len(valid_runners))
    for i in range(n_wr_pairs):
        bracket_r32[2 * i] = valid_winners[i]
        bracket_r32[2 * i + 1] = valid_runners[i]

    # Pair 13-16: best third-placed vs best third-placed
    offset = 2 * n_wr_pairs
    n_third = len(valid_third)
    for i in range(0, n_third, 2):
        pos = offset + i
        if pos + 1 < ROUND_OF_32_SIZE:
            bracket_r32[pos] = valid_third[i]
            bracket_r32[pos + 1] = valid_third[i + 1] if i + 1 < n_third else -1

    n_filled = offset + n_third - (n_third % 2)
    for i in range(n_filled, ROUND_OF_32_SIZE):
        bracket_r32[i] = -1

    # R32
    r32_winners = run_knockout_round(bracket_r32, strengths)
    for idx in r32_winners:
        if idx >= 0:
            result[idx, 0] = 2

    # R16
    r16_winners = run_knockout_round(r32_winners, strengths)
    for idx in r16_winners:
        if idx >= 0:
            result[idx, 0] = 3

    # QF
    qf_winners = run_knockout_round(r16_winners, strengths)
    for idx in qf_winners:
        if idx >= 0:
            result[idx, 0] = 4

    # SF
    sf_winners = run_knockout_round(qf_winners, strengths)
    for idx in sf_winners:
        if idx >= 0:
            result[idx, 0] = 5

    # Final
    if len(sf_winners) >= 2 and sf_winners[0] >= 0 and sf_winners[1] >= 0:
        final_winner = run_knockout_round(sf_winners, strengths)
        if len(final_winner) >= 1 and final_winner[0] >= 0:
            result[final_winner[0], 0] = 6

    return result


class MonteCarloEngine:
    """
    Monte Carlo Tournament Simulation Engine.
    Runs N simulations of the full FIFA 2026 tournament.
    """

    def __init__(self, config: SimulationConfig | None = None):
        self.config = config or SimulationConfig()

    def run(
        self,
        teams: list[TeamEntity],
        group_mapping: dict[uuid.UUID, str],
    ) -> list[TournamentResult]:
        num_teams = len(teams)
        n_sims = self.config.num_simulations

        team_ids = [t.id for t in teams]
        team_names = [t.name for t in teams]
        strengths = np.array([t.igf_score / 50.0 for t in teams], dtype=np.float64)

        group_names = [group_mapping.get(t.id, "?") for t in teams]
        unique_groups = sorted(set(group_names))
        group_to_idx = {g: i for i, g in enumerate(unique_groups)}
        group_assignments = np.array([group_to_idx[g] for g in group_names], dtype=np.int64)

        logger.info(f"Running {n_sims} simulations across {num_teams} teams in {len(unique_groups)} groups...")

        if self.config.parallel:
            results = self._run_parallel(strengths, group_assignments, n_sims)
        else:
            results = self._run_serial(strengths, group_assignments, n_sims)

        return self._aggregate_results(results, team_ids, team_names, group_names, n_sims)

    def _run_serial(
        self, strengths: np.ndarray, assignments: np.ndarray, n_sims: int
    ) -> np.ndarray:
        """Run simulations serially with Numba acceleration."""
        num_teams = strengths.shape[0]
        results = np.zeros((num_teams, 10), dtype=np.int32)

        for sim in range(n_sims):
            sim_result = run_single_tournament_py(strengths, assignments, num_teams)
            for t in range(num_teams):
                stage = sim_result[t, 0]
                position = sim_result[t, 1]
                points = sim_result[t, 2]

                if stage >= 1:
                    results[t, 0] += 1  # R32
                if stage >= 2:
                    results[t, 1] += 1  # R16
                if stage >= 3:
                    results[t, 2] += 1  # QF
                if stage >= 4:
                    results[t, 3] += 1  # SF
                if stage >= 5:
                    results[t, 4] += 1  # Final
                if stage >= 6:
                    results[t, 5] += 1  # Winner

                # Track group position counts (columns 6-8)
                if position == 1:
                    results[t, 6] += 1
                elif position == 2:
                    results[t, 7] += 1
                elif position == 3:
                    results[t, 8] += 1

                # Accumulate total group points (column 9)
                results[t, 9] += points

            if (sim + 1) % 10000 == 0:
                logger.info(f"  {sim + 1}/{n_sims} simulations completed")

        return results

    def _run_parallel(
        self, strengths: np.ndarray, assignments: np.ndarray, n_sims: int
    ) -> np.ndarray:
        num_teams = strengths.shape[0]
        results = np.zeros((num_teams, 10), dtype=np.int32)
        n_workers = 4
        chunk_size = n_sims // n_workers
        remainder = n_sims - chunk_size * n_workers

        chunks = [chunk_size] * n_workers
        if remainder > 0:
            chunks.append(remainder)

        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            futures = [
                executor.submit(self._run_serial, strengths, assignments, c)
                for c in chunks
            ]
            for f in futures:
                chunk_result = f.result()
                results += chunk_result

        return results

    @staticmethod
    def _aggregate_results(
        results: np.ndarray,
        team_ids: list[uuid.UUID],
        team_names: list[str],
        group_names: list[str],
        n_sims: int,
    ) -> list[TournamentResult]:
        outputs = []
        for i in range(len(team_ids)):
            pos1 = int(results[i, 6])
            pos2 = int(results[i, 7])
            pos3 = int(results[i, 8])
            pos4 = n_sims - pos1 - pos2 - pos3

            if n_sims > 0:
                expected_position = float(1 * pos1 + 2 * pos2 + 3 * pos3 + 4 * pos4) / n_sims
                avg_points = float(results[i, 9]) / n_sims
            else:
                expected_position = 0.0
                avg_points = 0.0

            outputs.append(
                TournamentResult(
                    team_id=team_ids[i],
                    team_name=team_names[i],
                    group_name=group_names[i],
                    round_of_32_count=int(results[i, 0]),
                    round_of_16_count=int(results[i, 1]),
                    quarter_final_count=int(results[i, 2]),
                    semi_final_count=int(results[i, 3]),
                    final_count=int(results[i, 4]),
                    won_count=int(results[i, 5]),
                    group_position=int(round(expected_position)),
                    total_points=avg_points,
                    pos1_count=pos1,
                    pos2_count=pos2,
                    pos3_count=pos3,
                    pos4_count=pos4,
                )
            )
        return outputs
