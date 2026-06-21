"""
Sprint 8 - FASE 2: Multi-Objective EliteScore.

Combines Accuracy, Brier, LogLoss, ECE, Stress Std, Pearson into a single
normalized metric for objective model selection.

Weights (sensitivity-based):
  - Accuracy: 0.25 (primary discriminability)
  - Brier: 0.25 (primary scoring rule)
  - LogLoss: 0.20 (secondary scoring rule)
  - ECE: 0.15 (calibration)
  - Stress Std: 0.10 (robustness)
  - Pearson: 0.05 (tournament alignment)
"""
from __future__ import annotations

import numpy as np


class EliteScore:
    """
    Multi-objective score combining discrimination + calibration + robustness.

    Higher is better (0 = worst, 1 = perfect).
    """

    # Default weights based on sensitivity analysis
    WEIGHTS = {
        "accuracy": 0.25,
        "brier": 0.25,
        "logloss": 0.20,
        "ece": 0.15,
        "stress_std": 0.10,
        "pearson": 0.05,
    }

    @staticmethod
    def normalize(value: float, lower: float, upper: float, higher_better: bool = True) -> float:
        """Min-max normalize to [0, 1]."""
        if upper <= lower:
            return 0.5
        normalized = (value - lower) / (upper - lower)
        if higher_better:
            return float(np.clip(normalized, 0, 1))
        else:
            return float(np.clip(1 - normalized, 0, 1))

    @classmethod
    def compute(cls, accuracy: float, brier: float, logloss: float,
                ece: float, stress_std: float, pearson: float,
                weights: dict[str, float] | None = None) -> dict:
        """
        Compute EliteScore from raw metrics.

        Reference ranges (from Sprint 3-7.5 empirical data):
          accuracy: [0.45, 0.55]  higher better
          brier:    [0.58, 0.65]  lower better
          logloss:  [0.95, 1.10]  lower better
          ece:      [0.02, 0.10]  lower better
          stress:   [0.05, 0.12]  lower better
          pearson:  [0.85, 1.00]  higher better
        """
        w = weights or cls.WEIGHTS

        n_acc = cls.normalize(accuracy, 0.45, 0.55, higher_better=True)
        n_brier = cls.normalize(brier, 0.58, 0.65, higher_better=False)
        n_logloss = cls.normalize(logloss, 0.95, 1.10, higher_better=False)
        n_ece = cls.normalize(ece, 0.02, 0.10, higher_better=False)
        n_stress = cls.normalize(stress_std, 0.05, 0.12, higher_better=False)
        n_pearson = cls.normalize(pearson, 0.85, 1.00, higher_better=True)

        score = (w.get("accuracy", 0) * n_acc + w.get("brier", 0) * n_brier
                 + w.get("logloss", 0) * n_logloss + w.get("ece", 0) * n_ece
                 + w.get("stress_std", 0) * n_stress + w.get("pearson", 0) * n_pearson)

        return {
            "elite_score": round(score, 4),
            "components": {
                "accuracy_raw": accuracy, "accuracy_norm": round(n_acc, 4),
                "brier_raw": brier, "brier_norm": round(n_brier, 4),
                "logloss_raw": logloss, "logloss_norm": round(n_logloss, 4),
                "ece_raw": ece, "ece_norm": round(n_ece, 4),
                "stress_std_raw": stress_std, "stress_norm": round(n_stress, 4),
                "pearson_raw": pearson, "pearson_norm": round(n_pearson, 4),
            },
            "weights": w,
        }

    @classmethod
    def compare_configs(cls, configs: list[dict]) -> list[dict]:
        """
        Rank multiple configs by EliteScore.

        Each config dict must have: label, accuracy, brier, logloss, ece, stress_std, pearson
        """
        scored = []
        for cfg in configs:
            result = cls.compute(
                cfg["accuracy"], cfg["brier"], cfg["logloss"],
                cfg["ece"], cfg["stress_std"], cfg["pearson"],
            )
            scored.append({**cfg, "elite_score": result["elite_score"],
                           "components": result["components"]})
        scored.sort(key=lambda x: -x["elite_score"])
        return scored
