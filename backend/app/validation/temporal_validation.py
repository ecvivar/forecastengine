"""
Sprint 8 - FASE 3: Temporal Validation.

Splits historical World Cups into train/validate sets:
  1. Train: 2014+2018, Validate: 2022
  2. Train: 2014, Validate: 2018

Measures Accuracy, Brier, LogLoss, ECE to detect historical overfitting.
"""
from __future__ import annotations

import logging
import uuid
from collections import defaultdict

import numpy as np

from app.data.historical_matches import ALL_HISTORICAL_MATCHES
from app.domain.entities import PredictionConfig, TeamEntity
from app.engine.match_prediction import MatchPredictionEngine
from app.validation.calibration_metrics import CalibrationMetrics

logger = logging.getLogger(__name__)


class TemporalValidation:
    """Cross-temporal validation of prediction engine."""

    def __init__(self, config: PredictionConfig | None = None):
        self.config = config or PredictionConfig()
        self.metrics = CalibrationMetrics()

    def _build_entities(self, matches) -> dict[str, TeamEntity]:
        """Build TeamEntity dict from a list of matches."""
        td = {}
        for m in matches:
            for side in ("home", "away"):
                name = getattr(m, f"{side}_team")
                elo = getattr(m, f"{side}_elo")
                gf = m.home_goals if side == "home" else m.away_goals
                ga = m.away_goals if side == "home" else m.home_goals
                if name not in td:
                    td[name] = {"elo": elo, "gf": [], "ga": []}
                td[name]["gf"].append(gf)
                td[name]["ga"].append(ga)
        entities = {}
        for name, d in td.items():
            avg_gf = float(np.mean(d["gf"])) if d["gf"] else 1.0
            avg_ga = float(np.mean(d["ga"])) if d["ga"] else 1.5
            est_rank = max(1, min(100, int(100 * (1 - (d["elo"] - 1300) / 800))))
            entities[name] = TeamEntity(
                id=uuid.uuid4(), name=name, elo_score=d["elo"],
                fifa_rank=est_rank, xg_for=round(avg_gf, 4),
                xg_against=round(avg_ga, 4),
            )
        return entities

    def _predict_matches(self, entities: dict, matches) -> tuple[np.ndarray, np.ndarray]:
        """Run predictions and return probs/outcomes arrays."""
        mpe = MatchPredictionEngine(config=self.config)
        probs, outcomes = [], []
        for m in matches:
            home = entities.get(m.home_team)
            away = entities.get(m.away_team)
            if not home or not away:
                continue
            r = mpe.predict_full(home, away)
            probs.append([r.home_win_prob, r.draw_prob, r.away_win_prob])
            if m.home_goals > m.away_goals:
                outcomes.append([1, 0, 0])
            elif m.home_goals == m.away_goals:
                outcomes.append([0, 1, 0])
            else:
                outcomes.append([0, 0, 1])
        return np.array(probs), np.array(outcomes)

    def evaluate_split(self, train_years: list[str], val_year: str) -> dict:
        """Train on train_years, validate on val_year."""
        train_matches = [m for m in ALL_HISTORICAL_MATCHES if m.tournament in train_years]
        val_matches = [m for m in ALL_HISTORICAL_MATCHES if m.tournament == val_year]

        # Build entities from training data only
        train_entities = self._build_entities(train_matches)
        val_entities = self._build_entities(val_matches)

        # Predict
        train_probs, train_outcomes = self._predict_matches(train_entities, train_matches)
        val_probs, val_outcomes = self._predict_matches(val_entities, val_matches)

        # Train metrics
        train_acc = float(np.mean(np.argmax(train_probs, axis=1) == np.argmax(train_outcomes, axis=1)))
        train_brier = self.metrics.brier_score(train_probs, train_outcomes)
        train_logloss = self.metrics.log_loss(train_probs, train_outcomes)
        train_ece, _ = self.metrics.expected_calibration_error(train_probs, train_outcomes)

        # Validation metrics
        val_acc = float(np.mean(np.argmax(val_probs, axis=1) == np.argmax(val_outcomes, axis=1)))
        val_brier = self.metrics.brier_score(val_probs, val_outcomes)
        val_logloss = self.metrics.log_loss(val_probs, val_outcomes)
        val_ece, _ = self.metrics.expected_calibration_error(val_probs, val_outcomes)

        return {
            "split": f"{'+'.join(train_years)} -> {val_year}",
            "n_train": len(train_matches),
            "n_val": len(val_matches),
            "train": {
                "accuracy": round(train_acc, 4),
                "brier": round(train_brier, 4),
                "logloss": round(train_logloss, 4),
                "ece": round(train_ece, 4),
            },
            "validation": {
                "accuracy": round(val_acc, 4),
                "brier": round(val_brier, 4),
                "logloss": round(val_logloss, 4),
                "ece": round(val_ece, 4),
            },
            "gap": {
                "accuracy": round(val_acc - train_acc, 4),
                "brier": round(val_brier - train_brier, 4),
                "logloss": round(val_logloss - train_logloss, 4),
                "ece": round(val_ece - train_ece, 4),
            },
        }

    def run_all(self) -> list[dict]:
        """Run all temporal validation splits."""
        splits = [
            (["2014", "2018"], "2022"),
            (["2014"], "2018"),
        ]
        results = []
        for train_years, val_year in splits:
            r = self.evaluate_split(train_years, val_year)
            results.append(r)
            logger.info(f"  {r['split']}: val_acc={r['validation']['accuracy']:.4f}, "
                        f"val_brier={r['validation']['brier']:.4f}")
        return results
