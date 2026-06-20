"""
Sprint 5 — FASE 3 & 4 & 6: Meta Ensemble, Confidence Intervals, Bootstrap.

MetaPredictionEngine combines 4 models with learned weights:
  A: Poisson-xG (attack/defense composite)
  B: Bayesian Elo (Elo-only via Bayesian prior)
  C: Dixon-Coles corrected Poisson
  D: Strength Differential (overall_rating ratio)

Bootstrap generates CI via 1000 resamples.
"""
import logging
import random
from copy import deepcopy

import numpy as np

from app.domain.entities import MatchPredictionResult, PredictionConfig, TeamEntity
from app.engine.match_prediction import MatchPredictionEngine

logger = logging.getLogger(__name__)


class MetaPredictionEngine:
    """
    Ensemble of 4 models with learned weights.
    """

    MODEL_NAMES = ["poisson_xg", "bayesian_elo", "dixon_coles", "strength_diff"]

    def __init__(self, config: PredictionConfig | None = None, weights: dict[str, float] | None = None):
        self.config = config or PredictionConfig()
        self.engine = MatchPredictionEngine(config=self.config)

        # Default: equal weights
        self.weights = weights or {m: 0.25 for m in self.MODEL_NAMES}
        self._normalize_weights()

    def _normalize_weights(self):
        total = sum(self.weights.values())
        if total > 0:
            for k in self.weights:
                self.weights[k] /= total

    def predict(self, home_team: TeamEntity, away_team: TeamEntity,
                home_advantage: bool = True) -> MatchPredictionResult:
        """
        Ensemble prediction: weighted average of 4 models.
        """
        predictions = self._all_predictions(home_team, away_team, home_advantage)
        probs = np.zeros(3)
        for name, pred in predictions.items():
            w = self.weights.get(name, 0.25)
            probs[0] += w * pred["home_win"]
            probs[1] += w * pred["draw"]
            probs[2] += w * pred["away_win"]
        probs /= probs.sum()

        full = self.engine.predict_full(home_team, away_team, home_advantage)
        full.home_win_prob = round(float(probs[0]), 4)
        full.draw_prob = round(float(probs[1]), 4)
        full.away_win_prob = round(float(probs[2]), 4)
        return full

    def _all_predictions(self, home_team: TeamEntity, away_team: TeamEntity,
                         home_advantage: bool) -> dict[str, dict]:
        """
        Run all 4 individual models and return their home/draw/away probabilities.
        """
        # A: Poisson-xG (no Elo prior, no DC)
        cfg_a = deepcopy(self.config)
        cfg_a.bayesian_prior_strength = 0.0
        cfg_a.dixon_coles_tau = 0.0
        engine_a = MatchPredictionEngine(config=cfg_a)
        r_a = engine_a.predict_full(home_team, away_team, home_advantage)

        # B: Bayesian Elo only (pure prior, no xG/FIFA)
        cfg_b = deepcopy(self.config)
        # neutralize xG → set to 1.5/1.5 (avg)
        home_b = deepcopy(home_team)
        away_b = deepcopy(away_team)
        home_b.xg_for = 1.5
        home_b.xg_against = 1.5
        away_b.xg_for = 1.5
        away_b.xg_against = 1.5
        home_b.fifa_rank = 100
        away_b.fifa_rank = 100
        engine_b = MatchPredictionEngine(config=cfg_b)
        r_b = engine_b.predict_full(home_b, away_b, home_advantage)

        # C: Dixon-Coles (current full engine)
        r_c = self.engine.predict_full(home_team, away_team, home_advantage)

        # D: Strength Differential (overall_rating ratio → win prob)
        ts_h = self.engine.compute_team_strength(home_team)
        ts_a = self.engine.compute_team_strength(away_team)
        strength_ratio = ts_h.overall_rating / max(ts_a.overall_rating, 0.001)
        logit = np.log(strength_ratio) * 2.0
        home_w = 1.0 / (1.0 + np.exp(-logit))
        away_w = 1.0 - home_w
        draw_d = 0.25 * (1 - abs(home_w - away_w))
        total_d = home_w + draw_d + away_w

        return {
            "poisson_xg": {"home_win": r_a.home_win_prob, "draw": r_a.draw_prob, "away_win": r_a.away_win_prob},
            "bayesian_elo": {"home_win": r_b.home_win_prob, "draw": r_b.draw_prob, "away_win": r_b.away_win_prob},
            "dixon_coles": {"home_win": r_c.home_win_prob, "draw": r_c.draw_prob, "away_win": r_c.away_win_prob},
            "strength_diff": {"home_win": float(home_w), "draw": float(draw_d), "away_win": float(away_w)},
        }

    def bootstrap_ci(self, home_team: TeamEntity, away_team: TeamEntity,
                     n_resamples: int = 1000, ci: float = 0.90,
                     home_advantage: bool = True,
                     perturb_signals: bool = True) -> dict:
        """
        Bootstrap confidence intervals.

        When perturb_signals=True (default), also perturbs input signals
        (Elo, xG) using each team's rating_deviation uncertainty, producing
        more realistic CI widths.

        Returns dict with point estimates and CI bounds.
        """
        probs_hw = []
        probs_d = []
        probs_aw = []
        for _ in range(n_resamples):
            w = {m: random.gauss(self.weights[m], self.weights[m] * 0.1)
                 for m in self.MODEL_NAMES}
            w = {k: max(v, 0.01) for k, v in w.items()}
            tw = sum(w.values())
            w = {k: v / tw for k, v in w.items()}

            if perturb_signals:
                h = deepcopy(home_team)
                a = deepcopy(away_team)
                for team_obj in [h, a]:
                    rd = getattr(team_obj, 'rating_deviation', None) or 50.0
                    noise_scale = max(0.05, rd / 100.0)
                    team_obj.elo_score = int(team_obj.elo_score * random.gauss(1.0, noise_scale * 0.1))
                    if team_obj.xg_for:
                        team_obj.xg_for *= random.gauss(1.0, noise_scale * 0.15)
                    if team_obj.xg_against:
                        team_obj.xg_against *= random.gauss(1.0, noise_scale * 0.15)
                    rank = team_obj.fifa_rank or 100
                    team_obj.fifa_rank = max(1, int(rank * random.gauss(1.0, noise_scale * 0.05)))
                preds = self._all_predictions(h, a, home_advantage)
            else:
                preds = self._all_predictions(home_team, away_team, home_advantage)

            hw = sum(w[k] * preds[k]["home_win"] for k in self.MODEL_NAMES)
            dr = sum(w[k] * preds[k]["draw"] for k in self.MODEL_NAMES)
            aw = sum(w[k] * preds[k]["away_win"] for k in self.MODEL_NAMES)
            total = hw + dr + aw
            probs_hw.append(hw / total)
            probs_d.append(dr / total)
            probs_aw.append(aw / total)

        alpha = (1.0 - ci) / 2.0
        result = {}
        for label, arr in [("home_win", probs_hw), ("draw", probs_d), ("away_win", probs_aw)]:
            arr_s = sorted(arr)
            lo = arr_s[int(alpha * len(arr_s))]
            hi = arr_s[int((1 - alpha) * len(arr_s))]
            result[label] = {
                "point": float(np.mean(arr)),
                "ci_lower": round(float(lo), 4),
                "ci_upper": round(float(hi), 4),
            }
        return result

    def individual_contributions(self, home_team: TeamEntity, away_team: TeamEntity,
                                 home_advantage: bool = True) -> dict:
        """Return each model's prediction and its contribution to the ensemble."""
        preds = self._all_predictions(home_team, away_team, home_advantage)
        contributions = {}
        for name in self.MODEL_NAMES:
            w = self.weights.get(name, 0)
            p = preds[name]
            contributions[name] = {
                "weight": round(w, 4),
                "home_win": round(p["home_win"], 4),
                "draw": round(p["draw"], 4),
                "away_win": round(p["away_win"], 4),
                "contribution_pct": round(w * 100, 1),
            }
        return contributions

    def learn_weights(self, matches: list[tuple[TeamEntity, TeamEntity, np.ndarray]],
                      n_trials: int = 500) -> dict:
        """
        Learn ensemble weights via random search minimizing Brier score.
        """
        from app.validation.calibration_metrics import CalibrationMetrics
        metrics = CalibrationMetrics()

        best_loss = float("inf")
        best_weights = None

        for _ in range(n_trials):
            raw = {m: random.uniform(0.05, 0.50) for m in self.MODEL_NAMES}
            total = sum(raw.values())
            trial_weights = {k: v / total for k, v in raw.items()}
            self.weights = trial_weights

            probs, outcomes = [], []
            for home, away, outcome in matches:
                r = self.predict(home, away)
                probs.append([r.home_win_prob, r.draw_prob, r.away_win_prob])
                outcomes.append(outcome)
            if not probs:
                continue

            loss = metrics.log_loss(np.array(probs), np.array(outcomes))
            if loss < best_loss:
                best_loss = loss
                best_weights = trial_weights.copy()

        self.weights = best_weights or self.weights
        return {"best_weights": best_weights, "best_log_loss": round(best_loss, 6)}
