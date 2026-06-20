"""
Match Prediction Engine v2 — Hybrid Model.

Integrates:
- Elo rating (40%)
- xG attack strength (30%)
- xG defense strength (20%)
- FIFA ranking (10%)

Architecture:
  TeamEntity (raw data)
      |
      v
  TeamStrength (attack, defense, overall)
      |
      v
  Poisson(attack * defense * home_advantage)
      |
      v
  Dixon-Coles (low-score correction)
      |
      v
  Bayesian update (reduced Elo prior)
      |
      v
  MatchPredictionResult

Monte Carlo uses overall_strength directly.
"""

import logging
from dataclasses import dataclass
from math import exp, factorial

import numpy as np

from app.domain.entities import (
    ConfidenceLevel,
    MatchPredictionResult,
    PredictionConfig,
    TeamEntity,
    TeamStrength,
)

logger = logging.getLogger(__name__)


class MatchPredictionEngine:
    """Computes match outcome probabilities using a hybrid Elo + xG model."""

    def __init__(self, config: PredictionConfig | None = None):
        self.config = config or PredictionConfig()

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def predict_full(
        self,
        home_team: TeamEntity,
        away_team: TeamEntity,
        home_advantage: bool = True,
    ) -> MatchPredictionResult:
        """
        Full prediction pipeline:
          1. TeamStrength for home & away
          2. Attack/defence Poisson → Dixon-Coles
          3. Bayesian update (reduced Elo prior)
          4. Confidence, Surprise Risk, betting markets
        """
        home_s = self._compute_team_strength(home_team)
        away_s = self._compute_team_strength(away_team)

        # Step 1 — Dixon-Coles adjusted prediction
        dc_result = self._predict_dixon_coles(home_s, away_s, home_advantage)

        # Step 2 — Bayesian update (reduced prior)
        bayes = self._bayesian_update(
            dc_result["home_win"],
            dc_result["draw"],
            dc_result["away_win"],
            home_team.elo_score,
            away_team.elo_score,
        )

        # Step 3 — Confidence Index
        confidence = self._compute_confidence(home_team, away_team, home_s, away_s)
        confidence_level = self._classify_confidence(confidence)

        # Step 3b — Calibration adjustments
        if self.config.calibration_adjustments:
            bayes = self._apply_calibration_adjustments(
                bayes["home_win"], bayes["draw"], bayes["away_win"],
            )

        # Step 4 — Surprise Risk
        surprise = self._compute_surprise_risk(
            bayes["home_win"], bayes["away_win"], bayes["draw"]
        )

        # Step 5 — Betting markets
        score_probs = dc_result.get("score_probs", {})
        btts = self._compute_btts(score_probs)
        over_25, under_25, over_35 = self._compute_goal_markets(score_probs)
        home_cs, away_cs = self._compute_clean_sheets(score_probs)

        # Step 6 — Top 10 scores
        top_10 = self._top_n_scores(score_probs)

        return MatchPredictionResult(
            match_id=home_team.id,
            home_team=home_team.name,
            away_team=away_team.name,
            home_win_prob=round(bayes["home_win"], 4),
            draw_prob=round(bayes["draw"], 4),
            away_win_prob=round(bayes["away_win"], 4),
            home_expected_goals=round(dc_result["lambda_home"], 4),
            away_expected_goals=round(dc_result["lambda_away"], 4),
            most_likely_score=top_10[0][0] if top_10 else "",
            score_probabilities=score_probs,
            top_10_scores=top_10,
            confidence_index=round(confidence, 2),
            confidence_level=confidence_level,
            surprise_risk=round(surprise, 4),
            btts_prob=round(btts, 4),
            over_25_prob=round(over_25, 4),
            over_35_prob=round(over_35, 4),
            under_25_prob=round(under_25, 4),
            home_clean_sheet=round(home_cs, 4),
            away_clean_sheet=round(away_cs, 4),
        )

    def predict_poisson(
        self,
        home_team: TeamEntity,
        away_team: TeamEntity,
        home_advantage: bool = True,
    ) -> MatchPredictionResult:
        """Pure Poisson prediction (no DC, no Bayesian)."""
        home_s = self._compute_team_strength(home_team)
        away_s = self._compute_team_strength(away_team)
        raw = self._compute_poisson_matrix(home_s, away_s, home_advantage)
        return MatchPredictionResult(
            match_id=home_team.id,
            home_team=home_team.name,
            away_team=away_team.name,
            home_win_prob=round(raw["home_win"], 4),
            draw_prob=round(raw["draw"], 4),
            away_win_prob=round(raw["away_win"], 4),
            home_expected_goals=round(raw["lambda_home"], 4),
            away_expected_goals=round(raw["lambda_away"], 4),
            most_likely_score=raw["most_likely"],
            score_probabilities=raw["score_probs"],
            top_10_scores=self._top_n_scores(raw["score_probs"]),
        )

    # ------------------------------------------------------------------
    # TEAM STRENGTH COMPUTATION (FASE 2 & 4)
    # ------------------------------------------------------------------

    def compute_team_strength(self, team: TeamEntity) -> TeamStrength:
        """Public entry — compute strength for a single team."""
        return self._compute_team_strength(team)

    def _compute_team_strength(self, team: TeamEntity) -> TeamStrength:
        """
        Sprint 5 dual rating: attack_rating and defense_rating evolve independently.

        attack_rating = composite of xG for, Elo, FIFA (weighted)
        defense_rating = composite of xG against, Elo, FIFA (weighted)
        overall_rating = weighted composite of all 4 signals
        uncertainty = from team.rating_deviation (Dynamic Elo)
        """
        elo_norm = team.elo_score / 1500.0

        if team.xg_for is not None and team.xg_for > 0:
            attack_xg = team.xg_for / 1.5
            attack_xg = max(0.3, min(3.0, attack_xg))
        else:
            attack_xg = 1.0

        if team.xg_against is not None and team.xg_against > 0:
            defense_xg = 1.5 / team.xg_against
            defense_xg = max(0.3, min(3.0, defense_xg))
        else:
            defense_xg = 1.0

        rank = team.fifa_rank or 100
        fifa_norm = max(0.7, min(1.3, 100.0 / rank))

        w = self.config
        mut = w.elo_weight + w.xg_attack_weight + w.xg_defense_weight + w.fifa_weight
        mut = max(mut, 0.001)
        overall_rating = (w.elo_weight * elo_norm + w.xg_attack_weight * attack_xg
                          + w.xg_defense_weight * defense_xg + w.fifa_weight * fifa_norm) / mut

        atk_w = w.xg_attack_weight + w.fifa_weight
        if atk_w > 0:
            attack_rating = (w.xg_attack_weight * attack_xg + w.fifa_weight * fifa_norm) / atk_w
        else:
            attack_rating = attack_xg

        def_w = w.xg_defense_weight + w.fifa_weight
        if def_w > 0:
            defense_rating = (w.xg_defense_weight * defense_xg + w.fifa_weight * fifa_norm) / def_w
        else:
            defense_rating = defense_xg

        uncertainty = team.rating_deviation / 100.0

        return TeamStrength(
            attack_strength=attack_rating,
            defense_strength=defense_rating,
            overall_strength=overall_rating,
            attack_rating=attack_rating,
            defense_rating=defense_rating,
            overall_rating=overall_rating,
            uncertainty=uncertainty,
        )

    # ------------------------------------------------------------------
    # POISSON (FASE 6 — attack/defence based)
    # ------------------------------------------------------------------

    def _compute_poisson_matrix(
        self,
        home_s: TeamStrength,
        away_s: TeamStrength,
        home_advantage: bool = True,
    ) -> dict:
        """
        λ_home = μ * attack_home * defense_away * home_factor
        λ_away = μ * attack_away * defense_home
        """
        mu = self.config.league_avg_goals
        ha = self.config.home_advantage if home_advantage else 0.0

        lambda_home = mu * home_s.attack_strength * away_s.defense_strength * (1.0 + ha)
        lambda_away = mu * away_s.attack_strength * home_s.defense_strength

        lambda_home = max(0.1, lambda_home)
        lambda_away = max(0.1, lambda_away)

        max_g = self.config.max_goals
        home_dist = np.array(
            [self._poisson_pmf(i, lambda_home) for i in range(max_g + 1)]
        )
        away_dist = np.array(
            [self._poisson_pmf(j, lambda_away) for j in range(max_g + 1)]
        )

        matrix = np.outer(home_dist, away_dist)

        away_win = np.sum(matrix[np.triu_indices(max_g + 1, k=1)])
        draw = np.sum(np.diag(matrix))
        home_win = np.sum(matrix[np.tril_indices(max_g + 1, k=-1)])

        total = home_win + draw + away_win
        if total > 0:
            home_win /= total
            draw /= total
            away_win /= total

        score_probs = {}
        for i in range(max_g + 1):
            for j in range(max_g + 1):
                score_probs[f"{i}-{j}"] = float(matrix[i, j] / total) if total > 0 else 0.0

        most_likely = self._most_likely_score(matrix)

        return {
            "home_win": home_win,
            "draw": draw,
            "away_win": away_win,
            "home_goal_dist": home_dist.tolist(),
            "away_goal_dist": away_dist.tolist(),
            "matrix": matrix,
            "score_probs": score_probs,
            "most_likely": most_likely,
            "lambda_home": lambda_home,
            "lambda_away": lambda_away,
        }

    def _predict_dixon_coles(
        self,
        home_s: TeamStrength,
        away_s: TeamStrength,
        home_advantage: bool = True,
    ) -> dict:
        """Poisson + Dixon-Coles correction."""
        raw = self._compute_poisson_matrix(home_s, away_s, home_advantage)
        rho = self.config.dixon_coles_tau
        adjusted = self._apply_dixon_coles(raw["score_probs"], rho)
        adjusted["lambda_home"] = raw["lambda_home"]
        adjusted["lambda_away"] = raw["lambda_away"]
        return adjusted

    # ------------------------------------------------------------------
    # STATIC HELPERS
    # ------------------------------------------------------------------

    @staticmethod
    def _poisson_pmf(k: int, lam: float) -> float:
        return (lam ** k) * exp(-lam) / factorial(k)

    @staticmethod
    def _most_likely_score(matrix: np.ndarray) -> str:
        idx = np.unravel_index(np.argmax(matrix), matrix.shape)
        return f"{idx[0]}-{idx[1]}"

    @staticmethod
    def _top_n_scores(
        score_probs: dict[str, float], n: int = 10
    ) -> list[tuple[str, float]]:
        sorted_scores = sorted(score_probs.items(), key=lambda x: x[1], reverse=True)
        return [(s, round(p, 6)) for s, p in sorted_scores[:n]]

    @staticmethod
    def _apply_dixon_coles(score_probs: dict[str, float], rho: float) -> dict:
        if not score_probs:
            return {"home_win": 0, "draw": 0, "away_win": 0, "most_likely": "", "score_probs": {}}

        adjusted = {}
        for score, prob in score_probs.items():
            i, j = map(int, score.split("-"))
            if i == 0 and j == 0:
                adjusted[score] = prob * (1 - rho)
            elif i == 0 and j == 1:
                adjusted[score] = prob * (1 + rho)
            elif i == 1 and j == 0:
                adjusted[score] = prob * (1 + rho)
            elif i == 1 and j == 1:
                adjusted[score] = prob * (1 - rho)
            else:
                adjusted[score] = prob

        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v / total for k, v in adjusted.items()}

        home_win = sum(v for k, v in adjusted.items() if int(k.split("-")[0]) > int(k.split("-")[1]))
        draw = sum(v for k, v in adjusted.items() if int(k.split("-")[0]) == int(k.split("-")[1]))
        away_win = sum(v for k, v in adjusted.items() if int(k.split("-")[0]) < int(k.split("-")[1]))
        most_likely = max(adjusted, key=adjusted.get)

        return {
            "home_win": home_win,
            "draw": draw,
            "away_win": away_win,
            "most_likely": most_likely,
            "score_probs": adjusted,
        }

    # ------------------------------------------------------------------
    # BAYESIAN UPDATE (FASE 5 — reduced prior)
    # ------------------------------------------------------------------

    def _bayesian_update(
        self,
        home_win: float,
        draw: float,
        away_win: float,
        elo_home: int,
        elo_away: int,
    ) -> dict:
        """
        Bayesian update using Elo difference as prior.

        Sprint 4A: elo_weight now scales the prior strength so that
        elo_weight directly affects predict_full().
        At default elo=0.40, ps = bayesian_prior_strength (0.5).
        At elo=0.60, ps = 0.75 (stronger Elo pull).
        At elo=0.20, ps = 0.25 (weaker Elo pull).
        """
        elo_diff = elo_home - elo_away
        if self.config.elo_compression_scale > 0:
            scale = self.config.elo_compression_scale
            elo_diff = np.tanh(elo_diff / scale) * scale
        elo_expected_home = 1.0 / (1.0 + 10.0 ** (-elo_diff / 400.0))

        prior_home = elo_expected_home
        prior_draw = 0.25
        prior_away = 1.0 - prior_home - prior_draw
        if prior_away < 0.0:
            prior_away = 0.0
            total_prior = prior_home + prior_draw + prior_away
            prior_home /= total_prior
            prior_draw /= total_prior

        base_ps = self.config.bayesian_prior_strength
        elo_scale = self.config.elo_weight / 0.40
        ps = base_ps * elo_scale
        total = ps + 1.0
        updated_home = (ps * prior_home + home_win) / total
        updated_draw = (ps * prior_draw + draw) / total
        updated_away = (ps * prior_away + away_win) / total

        total_p = updated_home + updated_draw + updated_away
        return {
            "home_win": updated_home / total_p,
            "draw": updated_draw / total_p,
            "away_win": updated_away / total_p,
        }

    # ------------------------------------------------------------------
    # CONFIDENCE & DERIVED METRICS
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_confidence(
        home_team: TeamEntity,
        away_team: TeamEntity,
        home_s: TeamStrength,
        away_s: TeamStrength,
    ) -> float:
        """Confidence Index 0-100 using multiple signal sources."""
        elo_diff = abs(home_team.elo_score - away_team.elo_score)
        elo_conf = min(100, elo_diff / 8.0)

        xg_diff = abs(
            (home_s.attack_strength - away_s.defense_strength)
            - (away_s.attack_strength - home_s.defense_strength)
        )
        xg_conf = min(100, xg_diff * 30.0)

        return 0.6 * elo_conf + 0.4 * xg_conf

    @staticmethod
    def _classify_confidence(score: float) -> str:
        if score >= 80:
            return ConfidenceLevel.MUY_ALTA.value
        if score >= 65:
            return ConfidenceLevel.ALTA.value
        if score >= 50:
            return ConfidenceLevel.MEDIA.value
        if score >= 35:
            return ConfidenceLevel.BAJA.value
        return ConfidenceLevel.MUY_BAJA.value

    @staticmethod
    def _apply_calibration_adjustments(
        home_win: float,
        draw: float,
        away_win: float,
        adjustments: dict | None = None,
    ) -> dict:
        adj = adjustments or {}
        hw, dw, aw = home_win, draw, away_win
        ha_adj = adj.get("home_advantage_adjustment", 0.0)
        if ha_adj != 0.0:
            hw *= 1.0 + ha_adj
            hw = max(0.0, hw)
        dr_adj = adj.get("draw_adjustment", 0.0)
        if dr_adj != 0.0:
            dw *= 1.0 + dr_adj
            dw = max(0.0, dw)
        total = hw + dw + aw
        if total > 0:
            hw /= total
            dw /= total
            aw /= total
        return {"home_win": hw, "draw": dw, "away_win": aw}

    @staticmethod
    def _compute_surprise_risk(home_win: float, away_win: float, draw: float) -> float:
        if home_win >= away_win and home_win >= draw:
            return draw + away_win
        if away_win >= home_win and away_win >= draw:
            return draw + home_win
        return min(home_win, away_win) + draw

    @staticmethod
    def _compute_btts(score_probs: dict[str, float]) -> float:
        btts = 0.0
        for score, prob in score_probs.items():
            i, j = map(int, score.split("-"))
            if i > 0 and j > 0:
                btts += prob
        return btts

    @staticmethod
    def _compute_goal_markets(
        score_probs: dict[str, float],
    ) -> tuple[float, float, float]:
        over_25 = 0.0
        over_35 = 0.0
        for score, prob in score_probs.items():
            i, j = map(int, score.split("-"))
            total = i + j
            if total >= 3:
                over_25 += prob
            if total >= 4:
                over_35 += prob
        under_25 = 1.0 - over_25
        return over_25, under_25, over_35

    @staticmethod
    def _compute_clean_sheets(
        score_probs: dict[str, float],
    ) -> tuple[float, float]:
        home_cs = 0.0
        away_cs = 0.0
        for score, prob in score_probs.items():
            i, j = map(int, score.split("-"))
            if j == 0:
                home_cs += prob
            if i == 0:
                away_cs += prob
        return home_cs, away_cs
