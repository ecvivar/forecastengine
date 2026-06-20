"""
Sprint 3 — FASE 1: Calibration Metrics.

Deterministic scoring rules for evaluating probabilistic predictions:
  - Brier Score
  - Log Loss (cross-entropy)
  - Ranked Probability Score (RPS) for 3-outcome football
  - Expected Calibration Error (ECE)

All methods are pure functions with no external state.
"""

import numpy as np


class CalibrationMetrics:
    """Collection of scoring rules for probabilistic football predictions."""

    @staticmethod
    def brier_score(
        probabilities: np.ndarray,
        outcomes: np.ndarray,
    ) -> float:
        """
        Brier Score = mean((p_i - o_i)^2) over N x K outcomes.
        
        Args:
            probabilities: (N, 3) array with [home, draw, away] probabilities
            outcomes: (N, 3) one-hot encoded true outcomes
        
        Returns:
            float: Brier Score (0 = perfect, 1 = worst, ~0.33 = uninformed)
        """
        return float(np.mean(np.sum((probabilities - outcomes) ** 2, axis=1)))

    @staticmethod
    def log_loss(
        probabilities: np.ndarray,
        outcomes: np.ndarray,
        eps: float = 1e-15,
    ) -> float:
        """
        Log Loss (cross-entropy) = -mean(sum(o_i * log(p_i))).
        
        Args:
            probabilities: (N, 3) predicted probabilities
            outcomes: (N, 3) one-hot true outcomes
            eps: small epsilon to avoid log(0)
        
        Returns:
            float: Log Loss (0 = perfect, unbounded worst)
        """
        p = np.clip(probabilities, eps, 1 - eps)
        return float(-np.mean(np.sum(outcomes * np.log(p), axis=1)))

    @staticmethod
    def ranked_probability_score(
        probabilities: np.ndarray,
        outcomes: np.ndarray,
    ) -> float:
        """
        Ranked Probability Score for ordered 3-outcome forecasts.
        
        RPS = mean of sum((cumsum(p) - cumsum(o))^2) / (K - 1)
        
        For football (home, draw, away), RPS ∈ [0, 1].
        
        Args:
            probabilities: (N, 3) predicted probabilities
            outcomes: (N, 3) one-hot true outcomes
        
        Returns:
            float: RPS (0 = perfect, 1 = worst)
        """
        cum_p = np.cumsum(probabilities, axis=1)
        cum_o = np.cumsum(outcomes, axis=1)
        squared_diff = (cum_p - cum_o) ** 2
        k = probabilities.shape[1]
        rps_per_match = np.sum(squared_diff, axis=1) / (k - 1)
        return float(np.mean(rps_per_match))

    @staticmethod
    def expected_calibration_error(
        probabilities: np.ndarray,
        outcomes: np.ndarray,
        n_bins: int = 10,
    ) -> tuple[float, list[dict]]:
        """
        Expected Calibration Error (ECE) for 3-outcome predictions.
        
        Groups predictions into n_bins by confidence, measures |accuracy - confidence|.
        
        Args:
            probabilities: (N, 3) predicted probabilities
            outcomes: (N, 3) one-hot true outcomes
            n_bins: number of equal-width confidence bins
        
        Returns:
            (ece, bins): ECE score and per-bin details
        """
        max_probs = np.max(probabilities, axis=1)
        predicted_classes = np.argmax(probabilities, axis=1)
        actual_classes = np.argmax(outcomes, axis=1)
        correct = (predicted_classes == actual_classes).astype(float)

        bin_edges = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        bin_details = []

        for i in range(n_bins):
            lo, hi = bin_edges[i], bin_edges[i + 1]
            if i == n_bins - 1:
                mask = (max_probs >= lo) & (max_probs <= hi)
            else:
                mask = (max_probs >= lo) & (max_probs < hi)

            count = int(np.sum(mask))
            if count == 0:
                continue

            bin_conf = float(np.mean(max_probs[mask]))
            bin_acc = float(np.mean(correct[mask]))
            bin_ece = abs(bin_acc - bin_conf)
            ece += bin_ece * (count / len(probabilities))

            bin_details.append({
                "bin_lower": round(lo, 2),
                "bin_upper": round(hi, 2),
                "count": count,
                "mean_confidence": round(bin_conf, 4),
                "mean_accuracy": round(bin_acc, 4),
                "gap": round(bin_ece, 4),
            })

        return round(ece, 6), bin_details
