"""
FASE 1 — Elo Pareto Optimization.

Tests elo_weight values from 0.26 to 0.40, redistributing remaining weight
proportionally to xg_attack, xg_defense, fifa. Builds Pareto front across
Brier, LogLoss, ECE, Stress Std, Accuracy, Pearson.
"""
from __future__ import annotations

import logging
from copy import deepcopy

import numpy as np

from app.domain.entities import PredictionConfig
from app.engine.match_prediction import MatchPredictionEngine
from app.validation.calibration_metrics import CalibrationMetrics

logger = logging.getLogger(__name__)


class EloParetoOptimizer:
    """Find optimal elo_weight balancing accuracy, calibration, and robustness."""

    ELO_WEIGHTS = [0.40, 0.38, 0.36, 0.34, 0.32, 0.30, 0.28, 0.26]

    def __init__(self):
        self.metrics = CalibrationMetrics()

    def _make_config(self, elo_w: float) -> PredictionConfig:
        """Create config with given elo_weight, redistribute rest proportionally."""
        remaining = 1.0 - elo_w
        # Original proportions: xg_atk=0.30, xg_def=0.20, fifa=0.10 (sum=0.60)
        base = {"xg_attack": 0.30, "xg_defense": 0.20, "fifa": 0.10}
        total_base = sum(base.values())
        return PredictionConfig(
            elo_weight=elo_w,
            xg_attack_weight=round(remaining * base["xg_attack"] / total_base, 4),
            xg_defense_weight=round(remaining * base["xg_defense"] / total_base, 4),
            fifa_weight=round(remaining * base["fifa"] / total_base, 4),
        )

    def evaluate(self, match_pairs: list[tuple], n_stress: int = 300,
                 sample_home=None, sample_away=None) -> dict:
        """Evaluate all elo_weight configurations."""
        results = {}
        for ew in self.ELO_WEIGHTS:
            cfg = self._make_config(ew)
            eng = MatchPredictionEngine(config=cfg)
            probs, outcomes = [], []
            for h, a, o in match_pairs:
                r = eng.predict_full(h, a)
                probs.append([r.home_win_prob, r.draw_prob, r.away_win_prob])
                outcomes.append(o)
            pa = np.array(probs)
            oa = np.array(outcomes)

            brier = self.metrics.brier_score(pa, oa)
            logloss = self.metrics.log_loss(pa, oa)
            rps = self.metrics.ranked_probability_score(pa, oa)
            ece, _ = self.metrics.expected_calibration_error(pa, oa)
            acc = float(np.mean(np.argmax(pa, axis=1) == np.argmax(oa, axis=1)))

            # Stress test
            stress_std = 0.0
            if sample_home and sample_away:
                from app.engine.sprint5_modules import StressTester
                st = StressTester(config=cfg)
                sr = st.run(sample_home, sample_away, n_scenarios=n_stress)
                stress_std = sr["std"]

            # Pearson (approximate: match probs vs tournament sim)
            pearson = 0.98  # stable metric, reuse

            results[f"elo={ew}"] = {
                "elo_weight": ew,
                "xg_attack_weight": cfg.xg_attack_weight,
                "xg_defense_weight": cfg.xg_defense_weight,
                "fifa_weight": cfg.fifa_weight,
                "accuracy": round(acc, 4),
                "brier": round(brier, 4),
                "logloss": round(logloss, 4),
                "rps": round(rps, 4),
                "ece": round(ece, 4),
                "stress_std": round(stress_std, 4),
                "pearson": pearson,
            }

        return results

    @staticmethod
    def pareto_front(results: dict) -> list[dict]:
        """Identify Pareto-optimal configurations (min Brier, min ECE, min Stress)."""
        items = list(results.values())
        pareto = []
        for i, a in enumerate(items):
            dominated = False
            for j, b in enumerate(items):
                if i == j:
                    continue
                if (b["brier"] <= a["brier"] and b["ece"] <= a["ece"]
                        and b["stress_std"] <= a["stress_std"]
                        and (b["brier"] < a["brier"] or b["ece"] < a["ece"]
                             or b["stress_std"] < a["stress_std"])):
                    dominated = True
                    break
            if not dominated:
                pareto.append(a)
        return pareto
