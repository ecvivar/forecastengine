"""
FASE 2 — Regional Probability Calibration.

Compares global (single Temperature/Platt) vs regional (5 independent calibrators
for 0-20%, 20-40%, 40-60%, 60-80%, 80-100% regions).
Each region gets its own Temperature or Platt scaling.
"""
from __future__ import annotations

import logging

import numpy as np
from scipy.optimize import minimize

from app.validation.calibration_metrics import CalibrationMetrics

logger = logging.getLogger(__name__)


class RegionalCalibrator:
    """Region-specific calibration using Temperature or Platt scaling."""

    REGIONS = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]

    def __init__(self):
        self.metrics = CalibrationMetrics()

    def temperature_scale(self, probs: np.ndarray, outcomes: np.ndarray) -> tuple[np.ndarray, float]:
        """Global temperature scaling."""
        def loss(T):
            scaled = np.zeros_like(probs)
            for i in range(3):
                logits = np.log(np.clip(probs[:, i], 1e-15, 1 - 1e-15))
                scaled[:, i] = np.exp(logits / T)
            scaled /= scaled.sum(axis=1, keepdims=True)
            return self.metrics.log_loss(scaled, outcomes)

        res = minimize(loss, x0=1.0, bounds=[(0.3, 3.0)], method="L-BFGS-B")
        T = float(res.x[0])
        scaled = np.zeros_like(probs)
        for i in range(3):
            logits = np.log(np.clip(probs[:, i], 1e-15, 1 - 1e-15))
            scaled[:, i] = np.exp(logits / T)
        scaled /= scaled.sum(axis=1, keepdims=True)
        return scaled, T

    def platt_scale(self, probs: np.ndarray, outcomes: np.ndarray) -> tuple[np.ndarray, float, float]:
        """Global Platt scaling (logit regression)."""
        from sklearn.linear_model import LogisticRegression
        scaled = np.zeros_like(probs)
        params = []
        for i in range(3):
            n_classes = len(np.unique(outcomes[:, i]))
            logits = np.log(np.clip(probs[:, i], 1e-15, 1 - 1e-15)).reshape(-1, 1)
            if n_classes < 2:
                scaled[:, i] = float(outcomes[:, i][0])
                params.append((0.0, 0.0))
            else:
                lr = LogisticRegression(C=1e6, solver="lbfgs")
                lr.fit(logits, outcomes[:, i])
                p = lr.predict_proba(logits)[:, 1]
                scaled[:, i] = p
                params.append((float(lr.coef_[0][0]), float(lr.intercept_[0])))
        scaled /= scaled.sum(axis=1, keepdims=True)
        return scaled, params

    def _region_mask(self, probs: np.ndarray, lo: float, hi: float) -> np.ndarray:
        """Mask for predictions where max probability falls in [lo, hi)."""
        max_p = np.max(probs, axis=1)
        return (max_p >= lo) & (max_p < hi)

    def regional_calibrate(self, probs: np.ndarray, outcomes: np.ndarray,
                           method: str = "temperature") -> tuple[np.ndarray, dict]:
        """
        Apply independent calibrators per probability region.
        Returns calibrated probabilities and region metadata.
        """
        calibrated = np.zeros_like(probs)
        region_info = {}

        for lo, hi in self.REGIONS:
            mask = self._region_mask(probs, lo, hi)
            count = int(np.sum(mask))
            if count == 0:
                region_info[f"{lo*100:.0f}-{hi*100:.0f}%"] = {"count": 0, "method": "none"}
                continue

            if method == "temperature":
                cal, T = self.temperature_scale(probs[mask], outcomes[mask])
                calibrated[mask] = cal
                region_info[f"{lo*100:.0f}-{hi*100:.0f}%"] = {"count": count, "T": round(T, 4)}
            elif method == "platt":
                cal, params = self.platt_scale(probs[mask], outcomes[mask])
                calibrated[mask] = cal
                region_info[f"{lo*100:.0f}-{hi*100:.0f}%"] = {"count": count, "params": [round(p, 4) for p in params[0]]}

        return calibrated, region_info

    def evaluate(self, probs: np.ndarray, outcomes: np.ndarray) -> dict:
        """Compare global vs regional calibration."""
        global_T, T = self.temperature_scale(probs, outcomes)
        global_P, P_params = self.platt_scale(probs, outcomes)
        regional_T, rt_info = self.regional_calibrate(probs, outcomes, method="temperature")
        regional_P, rp_info = self.regional_calibrate(probs, outcomes, method="platt")

        baseline = {
            "brier": round(self.metrics.brier_score(probs, outcomes), 4),
            "logloss": round(self.metrics.log_loss(probs, outcomes), 4),
            "ece": round(self.metrics.expected_calibration_error(probs, outcomes)[0], 4),
        }
        gt = {
            "brier": round(self.metrics.brier_score(global_T, outcomes), 4),
            "logloss": round(self.metrics.log_loss(global_T, outcomes), 4),
            "ece": round(self.metrics.expected_calibration_error(global_T, outcomes)[0], 4),
            "T": round(T, 4),
        }
        gp = {
            "brier": round(self.metrics.brier_score(global_P, outcomes), 4),
            "logloss": round(self.metrics.log_loss(global_P, outcomes), 4),
            "ece": round(self.metrics.expected_calibration_error(global_P, outcomes)[0], 4),
        }
        rt = {
            "brier": round(self.metrics.brier_score(regional_T, outcomes), 4),
            "logloss": round(self.metrics.log_loss(regional_T, outcomes), 4),
            "ece": round(self.metrics.expected_calibration_error(regional_T, outcomes)[0], 4),
            "regions": rt_info,
        }
        rp = {
            "brier": round(self.metrics.brier_score(regional_P, outcomes), 4),
            "logloss": round(self.metrics.log_loss(regional_P, outcomes), 4),
            "ece": round(self.metrics.expected_calibration_error(regional_P, outcomes)[0], 4),
            "regions": rp_info,
        }

        return {
            "baseline": baseline,
            "global_temperature": gt,
            "global_platt": gp,
            "regional_temperature": rt,
            "regional_platt": rp,
        }
