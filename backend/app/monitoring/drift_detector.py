from __future__ import annotations
import numpy as np
from scipy.stats import entropy
from scipy.spatial.distance import jensenshannon
from typing import Optional


class DriftDetector:
    def __init__(self, psi_threshold: float = 0.10, kl_threshold: float = 0.10, js_threshold: float = 0.05):
        self.psi_threshold = psi_threshold
        self.kl_threshold = kl_threshold
        self.js_threshold = js_threshold

    def psi(self, actual: np.ndarray, expected: np.ndarray, n_bins: int = 10) -> float:
        bins = np.linspace(0, 1, n_bins + 1)
        actual_binned = np.histogram(actual, bins=bins, density=True)[0] + 1e-10
        expected_binned = np.histogram(expected, bins=bins, density=True)[0] + 1e-10
        actual_binned = actual_binned / actual_binned.sum()
        expected_binned = expected_binned / expected_binned.sum()
        return float(np.sum((actual_binned - expected_binned) * np.log(actual_binned / expected_binned)))

    def kl_divergence(self, p: np.ndarray, q: np.ndarray) -> float:
        p = np.asarray(p) + 1e-10
        q = np.asarray(q) + 1e-10
        p = p / p.sum()
        q = q / q.sum()
        return float(entropy(p, q))

    def js_divergence(self, p: np.ndarray, q: np.ndarray) -> float:
        p = np.asarray(p) + 1e-10
        q = np.asarray(q) + 1e-10
        return float(jensenshannon(p, q, base=2))

    def detect_distribution_drift(
        self,
        actual: np.ndarray,
        expected: np.ndarray,
        label: str = "unknown",
    ) -> dict:
        psi_val = self.psi(actual, expected)
        kl_val = self.kl_divergence(actual, expected)
        js_val = self.js_divergence(actual, expected)

        alerts = []
        if psi_val > self.psi_threshold:
            alerts.append(f"PSI={psi_val:.4f} > {self.psi_threshold}")
        if kl_val > self.kl_threshold:
            alerts.append(f"KL={kl_val:.4f} > {self.kl_threshold}")
        if js_val > self.js_threshold:
            alerts.append(f"JS={js_val:.4f} > {self.js_threshold}")

        return {
            "label": label,
            "psi": round(psi_val, 6),
            "kl_divergence": round(kl_val, 6),
            "js_divergence": round(js_val, 6),
            "drift_detected": len(alerts) > 0,
            "alerts": alerts,
        }

    def detect_elo_drift(
        self,
        current_elos: np.ndarray,
        reference_elos: np.ndarray,
    ) -> dict:
        return self.detect_distribution_drift(current_elos, reference_elos, label="elo")

    def detect_prediction_drift(
        self,
        current_preds: np.ndarray,
        reference_preds: np.ndarray,
    ) -> dict:
        return self.detect_distribution_drift(current_preds, reference_preds, label="prediction")

    def detect_uncertainty_drift(
        self,
        current_uncertainty: np.ndarray,
        reference_uncertainty: np.ndarray,
    ) -> dict:
        return self.detect_distribution_drift(current_uncertainty, reference_uncertainty, label="uncertainty")

    def full_check(
        self,
        current_elos: np.ndarray,
        reference_elos: np.ndarray,
        current_preds: np.ndarray,
        reference_preds: np.ndarray,
        current_uncertainty: np.ndarray,
        reference_uncertainty: np.ndarray,
    ) -> dict:
        return {
            "elo": self.detect_elo_drift(current_elos, reference_elos),
            "prediction": self.detect_prediction_drift(current_preds, reference_preds),
            "uncertainty": self.detect_uncertainty_drift(current_uncertainty, reference_uncertainty),
            "any_drift": False,
        }
