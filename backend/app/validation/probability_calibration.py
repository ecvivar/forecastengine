"""
Sprint 4A — FASE 4: Probability Calibration Module.

Three calibration methods for 3-outcome football predictions:
  - Platt Scaling (logistic regression on logits)
  - Isotonic Regression (PAVA-based binning)
  - Temperature Scaling (single T parameter)

All methods are deterministic and operate on (N, 3) probability arrays.
"""
import numpy as np
from scipy.optimize import minimize, fminbound


class ProbabilityCalibrator:
    """Calibrate 3-outcome match probabilities using post-hoc methods."""

    @staticmethod
    def platt_scaling(
        probabilities: np.ndarray,
        outcomes: np.ndarray,
    ) -> tuple[np.ndarray, dict]:
        """
        Platt scaling via logistic regression on logits.

        Learns parameters a, b such that:
          P'(y=1|x) = 1 / (1 + exp(-(a * logit(x) + b)))

        Args:
            probabilities: (N, 3) predicted probabilities
            outcomes: (N, 3) one-hot encoded outcomes

        Returns:
            (calibrated_probs, params) where params = {"a": float, "b": float}
        """
        max_probs = np.max(probabilities, axis=1)
        y = (np.argmax(probabilities, axis=1) == np.argmax(outcomes, axis=1)).astype(float)
        logits = np.log(
            np.clip(max_probs, 1e-15, 1 - 1e-15)
            / (1 - np.clip(max_probs, 1e-15, 1 - 1e-15))
        )

        def _nll(params):
            a, b = params
            scaled = 1.0 / (1.0 + np.exp(-(a * logits + b)))
            scaled = np.clip(scaled, 1e-15, 1 - 1e-15)
            return -np.mean(y * np.log(scaled) + (1 - y) * np.log(1 - scaled))

        result = minimize(_nll, [1.0, 0.0], method="Nelder-Mead")
        a, b = result.x

        scaled = probabilities.copy()
        for i in range(len(scaled)):
            pred_class = np.argmax(scaled[i])
            conf = max_probs[i]
            logit = np.log(max(1e-15, conf / (1 - conf)))
            new_conf = 1.0 / (1.0 + np.exp(-(a * logit + b)))
            conf_ratio = new_conf / max(conf, 1e-15)
            scaled[i] = scaled[i] * conf_ratio
            scaled[i] = np.clip(scaled[i], 1e-15, 1 - 1e-15)
            scaled[i] /= scaled[i].sum()

        return scaled, {"a": round(float(a), 4), "b": round(float(b), 4)}

    @staticmethod
    def isotonic_regression(
        probabilities: np.ndarray,
        outcomes: np.ndarray,
        n_bins: int = 20,
    ) -> tuple[np.ndarray, dict]:
        """
        Isotonic regression via bin-based PAVA.

        Groups predictions into n_bins by confidence, computes empirical
        accuracy per bin, and enforces monotonicity via pool-adjacent-violators.

        Args:
            probabilities: (N, 3) predicted probabilities
            outcomes: (N, 3) one-hot encoded outcomes
            n_bins: number of confidence bins

        Returns:
            (calibrated_probs, bin_info)
        """
        max_probs = np.max(probabilities, axis=1)
        y_correct = (np.argmax(probabilities, axis=1) == np.argmax(outcomes, axis=1)).astype(float)

        order = np.argsort(max_probs)
        sorted_p = max_probs[order]
        sorted_y = y_correct[order]

        bins = np.linspace(0, 1, n_bins + 1)
        bin_means = np.zeros(n_bins)
        bin_counts = np.zeros(n_bins)

        for i in range(n_bins):
            lo, hi = bins[i], bins[i + 1]
            if i == n_bins - 1:
                mask = (sorted_p >= lo) & (sorted_p <= hi)
            else:
                mask = (sorted_p >= lo) & (sorted_p < hi)
            cnt = int(np.sum(mask))
            bin_counts[i] = cnt
            if cnt > 0:
                bin_means[i] = float(np.mean(sorted_y[mask]))
            else:
                bin_means[i] = bins[i] + 0.5 / n_bins

        # Enforce monotonicity via PAVA
        changed = True
        while changed:
            changed = False
            for i in range(1, n_bins):
                if bin_counts[i] > 0 and bin_counts[i - 1] > 0:
                    if bin_means[i] < bin_means[i - 1]:
                        pooled = (bin_means[i] * bin_counts[i] + bin_means[i - 1] * bin_counts[i - 1]) / (
                            bin_counts[i] + bin_counts[i - 1]
                        )
                        bin_means[i - 1] = bin_means[i] = pooled
                        changed = True

        calibrated = probabilities.copy()
        for i in range(len(calibrated)):
            conf = max_probs[i]
            bin_idx = min(n_bins - 1, int(conf * n_bins))
            cal_conf = bin_means[bin_idx]
            conf_ratio = max(cal_conf / max(conf, 1e-15), 0.01)
            calibrated[i] = calibrated[i] * conf_ratio
            calibrated[i] = np.clip(calibrated[i], 1e-15, 1 - 1e-15)
            calibrated[i] /= calibrated[i].sum()

        return calibrated, {"n_bins": n_bins}

    @staticmethod
    def temperature_scaling(
        probabilities: np.ndarray,
        outcomes: np.ndarray,
    ) -> tuple[np.ndarray, dict]:
        """
        Temperature scaling: P = softmax(logits / T).

        Optimizes T > 0 to minimize negative log-likelihood.

        Args:
            probabilities: (N, 3) predicted probabilities
            outcomes: (N, 3) one-hot encoded outcomes

        Returns:
            (calibrated_probs, params) where params = {"T": float}
        """
        logits = np.log(np.clip(probabilities, 1e-15, 1 - 1e-15))

        def _nll(T):
            scaled = np.exp(logits / T)
            scaled /= scaled.sum(axis=1, keepdims=True)
            return -np.mean(
                np.sum(outcomes * np.log(np.clip(scaled, 1e-15, 1)), axis=1)
            )

        result = fminbound(lambda t: _nll(max(t, 0.01)), 0.1, 10.0, full_output=True)
        T = result[0]
        scaled = np.exp(logits / T)
        scaled /= scaled.sum(axis=1, keepdims=True)
        return scaled, {"T": round(float(T), 4)}
