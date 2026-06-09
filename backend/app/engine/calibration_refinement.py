"""
Calibration Refinement Engine.

Phase 5A: Deep analysis, probability calibration methods, bias reduction.
"""

import logging
import uuid
from copy import deepcopy

import numpy as np
from scipy.optimize import minimize
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from app.data.historical_matches import ALL_HISTORICAL_MATCHES
from app.domain.calibration import CalibrationMetric, HistoricalMatchData
from app.domain.calibration_refinement import (
    BiasReductionResult,
    CalibrationMethodResult,
    ProbabilityBucket,
    RefinementReport,
    ReliabilityCurve,
)
from app.domain.entities import TeamEntity
from app.engine.calibration import CalibrationEngine
from app.engine.match_prediction import MatchPredictionEngine

logger = logging.getLogger(__name__)

Outcome = tuple[int, int, int]

N_FOLDS = 5
EPS = 1e-15


class ReliabilityAnalyzer:
    """Compute reliability curves and probability bucket statistics."""

    @staticmethod
    def compute_curves(pred_probs: np.ndarray, actuals: np.ndarray) -> list[ReliabilityCurve]:
        curves = []

        # Max-confidence curve (existing calibration curve + buckets)
        max_conf = np.max(pred_probs, axis=1)
        correct = np.argmax(pred_probs, axis=1) == np.argmax(actuals, axis=1)
        curves.append(ReliabilityCurve(
            outcome="max_confidence",
            buckets=ReliabilityAnalyzer._bucketize(max_conf, correct),
        ))

        # Per-outcome curves
        labels = ["home", "draw", "away"]
        for c in range(3):
            outcome_probs = pred_probs[:, c]
            outcome_actual = actuals[:, c]
            curves.append(ReliabilityCurve(
                outcome=labels[c],
                buckets=ReliabilityAnalyzer._bucketize(outcome_probs, outcome_actual),
            ))

        return curves

    @staticmethod
    def _bucketize(values: np.ndarray, targets: np.ndarray) -> list[ProbabilityBucket]:
        """Divide [0,1] into 10 buckets and compute stats per bucket."""
        buckets = []
        for i in range(10):
            lo = i / 10.0
            hi = (i + 1) / 10.0
            mask = (values > lo) & (values <= hi)
            if i == 0:
                mask = mask | (values == lo)
            count = int(np.sum(mask))
            if count == 0:
                continue
            mean_pred = float(np.mean(values[mask]))
            obs_freq = float(np.mean(targets[mask]))
            abs_err = abs(mean_pred - obs_freq)
            rel_err = abs_err / (obs_freq + EPS)
            buckets.append(ProbabilityBucket(
                bucket_label=f"{int(lo*100)}-{int(hi*100)}%",
                lower=lo, upper=hi, count=count,
                mean_predicted=round(mean_pred, 4),
                observed_frequency=round(obs_freq, 4),
                absolute_error=round(abs_err, 4),
                relative_error=round(rel_err, 4),
            ))
        return buckets


class ProbabilisticCalibrator:
    """
    Probability calibration methods using cross-validation.

    Methods:
    - isotonic: Isotonic Regression (non-parametric)
    - platt: Platt Scaling (logistic regression on log-odds)
    - temperature: Temperature Scaling (single parameter T)
    """

    @staticmethod
    def calibrate(
        pred_probs: np.ndarray, actuals: np.ndarray,
        method: str = "isotonic",
    ) -> tuple[np.ndarray, dict]:
        """Calibrate probabilities. Returns (calibrated_probs, params)."""
        if method == "isotonic":
            return ProbabilisticCalibrator._isotonic_calibration(pred_probs, actuals)
        elif method == "platt":
            return ProbabilisticCalibrator._platt_calibration(pred_probs, actuals)
        elif method == "temperature":
            return ProbabilisticCalibrator._temperature_calibration(pred_probs, actuals)
        else:
            raise ValueError(f"Unknown method: {method}")

    @staticmethod
    def calibrate_cv(
        pred_probs: np.ndarray, actuals: np.ndarray,
        method: str = "isotonic", n_folds: int = N_FOLDS,
    ) -> tuple[np.ndarray, dict]:
        """
        Cross-validated calibration.
        Returns out-of-fold calibrated probabilities and averaged params.
        """
        n = len(pred_probs)
        indices = np.random.RandomState(42).permutation(n)
        fold_size = n // n_folds
        calibrated = np.zeros_like(pred_probs)
        all_params: list[dict] = []

        for k in range(n_folds):
            val_start = k * fold_size
            val_end = val_start + fold_size if k < n_folds - 1 else n
            val_idx = indices[val_start:val_end]
            train_idx = np.concatenate([indices[:val_start], indices[val_end:]])

            train_pred = pred_probs[train_idx]
            train_act = actuals[train_idx]
            val_pred = pred_probs[val_idx]

            cal_pred, params = ProbabilisticCalibrator.calibrate(train_pred, train_act, method)
            # Apply to validation set
            cal_val, _ = ProbabilisticCalibrator._apply_calibration(val_pred, method, params)
            calibrated[val_idx] = cal_val
            all_params.append(params)

        # Average params
        avg_params: dict = {}
        if all_params:
            for key in all_params[0]:
                vals = [p[key] for p in all_params]
                if isinstance(vals[0], (int, float)):
                    avg_params[key] = round(float(np.mean(vals)), 4)
                else:
                    avg_params[key] = vals[0]

        return calibrated, avg_params

    @staticmethod
    def _prob_to_logit(p: np.ndarray) -> np.ndarray:
        """Convert probabilities to log-odds (logit)."""
        p = np.clip(p, EPS, 1 - EPS)
        return np.log(p / (1 - p))

    @staticmethod
    def _softmax(z: np.ndarray, T: float = 1.0) -> np.ndarray:
        """Temperature-scaled softmax."""
        z_scaled = z / T
        z_scaled = z_scaled - np.max(z_scaled, axis=1, keepdims=True)
        exp_z = np.exp(z_scaled)
        return exp_z / np.sum(exp_z, axis=1, keepdims=True)

    @staticmethod
    def _prob_to_logits(p: np.ndarray) -> np.ndarray:
        """Inverse softmax: convert probs to logits."""
        p = np.clip(p, EPS, 1 - EPS)
        logits = np.log(p)
        logits = logits - np.mean(logits, axis=1, keepdims=True)
        return logits

    # ---- Isotonic Regression ----

    @staticmethod
    def _isotonic_calibration(
        pred_probs: np.ndarray, actuals: np.ndarray,
    ) -> tuple[np.ndarray, dict]:
        n_classes = pred_probs.shape[1]
        cal_probs = np.zeros_like(pred_probs)
        xs, ys = [], []
        for c in range(n_classes):
            iso = IsotonicRegression(out_of_bounds="clip")
            iso.fit(pred_probs[:, c], actuals[:, c])
            cal_probs[:, c] = iso.transform(pred_probs[:, c])
            # Store raw data for reconstruction
            xs.append(pred_probs[:, c].tolist())
            ys.append(actuals[:, c].tolist())

        row_sums = np.maximum(cal_probs.sum(axis=1, keepdims=True), EPS)
        cal_probs = cal_probs / row_sums

        params = {
            "type": "isotonic",
            "n_classes": n_classes,
            "xs": xs,
            "ys": ys,
        }
        return cal_probs, params

    # ---- Platt Scaling ----

    @staticmethod
    def _platt_calibration(
        pred_probs: np.ndarray, actuals: np.ndarray,
    ) -> tuple[np.ndarray, dict]:
        n_classes = pred_probs.shape[1]
        cal_probs = np.zeros_like(pred_probs)
        models = []
        for c in range(n_classes):
            logits = ProbabilisticCalibrator._prob_to_logit(pred_probs[:, c]).reshape(-1, 1)
            lr = LogisticRegression(C=1e6, solver="lbfgs")
            lr.fit(logits, actuals[:, c])
            cal_logits = lr.predict_proba(logits)[:, 1]
            cal_probs[:, c] = cal_logits
            models.append(lr)

        # Renormalize
        row_sums = cal_probs.sum(axis=1, keepdims=True)
        row_sums = np.maximum(row_sums, EPS)
        cal_probs = cal_probs / row_sums

        params = {
            "type": "platt",
            "n_classes": n_classes,
            "coefs": [float(m.coef_[0, 0]) for m in models],
            "intercepts": [float(m.intercept_[0]) for m in models],
        }
        return cal_probs, params

    # ---- Temperature Scaling ----

    @staticmethod
    def _temperature_calibration(
        pred_probs: np.ndarray, actuals: np.ndarray,
    ) -> tuple[np.ndarray, dict]:
        logits = ProbabilisticCalibrator._prob_to_logits(pred_probs)

        def nll(T: float) -> float:
            cal = ProbabilisticCalibrator._softmax(logits, T=max(T, EPS))
            eps = 1e-15
            cal = np.clip(cal, eps, 1 - eps)
            nll_val = -np.mean(np.sum(actuals * np.log(cal), axis=1))
            return nll_val

        result = minimize(nll, x0=[1.0], bounds=[(0.01, 10.0)], method="L-BFGS-B")
        T_opt = float(result.x[0])

        cal_probs = ProbabilisticCalibrator._softmax(logits, T=T_opt)

        params = {"type": "temperature", "temperature": round(T_opt, 4)}
        return cal_probs, params

    # ---- Apply calibration to new data ----

    @staticmethod
    def _apply_calibration(
        pred_probs: np.ndarray, method: str, params: dict,
    ) -> tuple[np.ndarray, dict]:
        """Apply a previously fitted calibration to new predictions."""
        if method == "isotonic":
            return ProbabilisticCalibrator._apply_isotonic(pred_probs, params)
        elif method == "platt":
            return ProbabilisticCalibrator._apply_platt(pred_probs, params)
        elif method == "temperature":
            return ProbabilisticCalibrator._apply_temperature(pred_probs, params)
        else:
            return pred_probs, params

    @staticmethod
    def _apply_isotonic(pred_probs: np.ndarray, params: dict) -> tuple[np.ndarray, dict]:
        n_classes = params["n_classes"]
        cal_probs = np.zeros_like(pred_probs)
        for c in range(n_classes):
            xs = np.array(params["xs"][c])
            ys = np.array(params["ys"][c])
            order = np.argsort(xs)
            xs_sorted = xs[order]
            ys_sorted = ys[order]
            cal_probs[:, c] = np.interp(
                pred_probs[:, c], xs_sorted, ys_sorted,
                left=ys_sorted[0], right=ys_sorted[-1],
            )
        row_sums = np.maximum(cal_probs.sum(axis=1, keepdims=True), EPS)
        cal_probs = cal_probs / row_sums
        return cal_probs, params

    @staticmethod
    def _apply_platt(pred_probs: np.ndarray, params: dict) -> tuple[np.ndarray, dict]:
        n_classes = params["n_classes"]
        cal_probs = np.zeros_like(pred_probs)
        for c in range(n_classes):
            logits = ProbabilisticCalibrator._prob_to_logit(pred_probs[:, c]).reshape(-1, 1)
            lr = LogisticRegression(C=1e6, solver="lbfgs")
            lr.coef_ = np.array([[params["coefs"][c]]])
            lr.intercept_ = np.array([params["intercepts"][c]])
            lr.classes_ = np.array([0, 1])
            cal_probs[:, c] = lr.predict_proba(logits)[:, 1]
        row_sums = np.maximum(cal_probs.sum(axis=1, keepdims=True), EPS)
        cal_probs = cal_probs / row_sums
        return cal_probs, params

    @staticmethod
    def _apply_temperature(pred_probs: np.ndarray, params: dict) -> tuple[np.ndarray, dict]:
        T = params["temperature"]
        logits = ProbabilisticCalibrator._prob_to_logits(pred_probs)
        cal_probs = ProbabilisticCalibrator._softmax(logits, T=T)
        return cal_probs, params


class BiasValidator:
    """Validate bias reduction adjustments against historical data."""

    @staticmethod
    def test_adjustment(
        historical_matches: list[HistoricalMatchData],
        adjustment_name: str, adjustment_value: float,
        base_config: dict | None = None,
    ) -> BiasReductionResult:
        """Test a single adjustment. Returns before/after comparison."""
        config = dict(base_config or {})
        engine = MatchPredictionEngine()
        cal_engine = CalibrationEngine(engine)

        # Before
        report_before = cal_engine.calibrate(historical_matches, home_advantage=False, model_type="full")
        before_brier = report_before.overall.brier_score
        before_ece = report_before.overall.calibration_error

        # Apply adjustment
        adj_config = dict(config)
        adj_config.update({adjustment_name: adjustment_value})
        if hasattr(engine.config, "calibration_adjustments"):
            engine.config.calibration_adjustments = adj_config
        else:
            from app.engine.match_prediction import MatchPredictionConfig
            engine.config = MatchPredictionConfig(calibration_adjustments=adj_config)

        report_after = cal_engine.calibrate(historical_matches, home_advantage=False, model_type="full")
        after_brier = report_after.overall.brier_score
        after_ece = report_after.overall.calibration_error

        brier_imp = ((before_brier - after_brier) / max(before_brier, 1e-10)) * 100
        applied = after_brier < before_brier

        return BiasReductionResult(
            adjustment_name=adjustment_name,
            before_metric=round(before_brier, 4),
            after_metric=round(after_brier, 4),
            improvement=round(brier_imp, 2),
            applied=applied,
        )

    @staticmethod
    def find_best_adjustments(
        historical_matches: list[HistoricalMatchData],
    ) -> list[BiasReductionResult]:
        """Test all candidate adjustments and return validated ones."""
        candidates = [
            ("home_advantage_adjustment", -0.01),
            ("home_advantage_adjustment", -0.02),
            ("home_advantage_adjustment", -0.03),
            ("draw_adjustment", -0.005),
            ("draw_adjustment", -0.01),
            ("draw_adjustment", -0.015),
            ("draw_adjustment", -0.02),
            ("favorite_calibration_factor", 0.95),
            ("favorite_calibration_factor", 0.90),
        ]

        results = []
        for name, val in candidates:
            result = BiasValidator.test_adjustment(historical_matches, name, val)
            results.append(result)

        return results


class CalibrationRefinementEngine:
    """Orchestrates reliability analysis, calibration fitting, and bias reduction."""

    def __init__(self):
        self.cal_engine = CalibrationEngine()
        self.pred_engine = self.cal_engine.prediction_engine

    def run_full_refinement(
        self,
        historical_matches: list[HistoricalMatchData] | None = None,
        home_advantage: bool = False,
    ) -> RefinementReport:
        matches = historical_matches or ALL_HISTORICAL_MATCHES
        report = RefinementReport()

        # 1. Generate predictions for all models
        models_data = self._generate_all_predictions(matches, home_advantage)
        full_probs = models_data["full"]["probs"]
        full_actuals = models_data["full"]["actuals"]

        # 2. Reliability analysis on Full Model
        report.reliability_curves = ReliabilityAnalyzer.compute_curves(full_probs, full_actuals)

        # 3. Test calibration methods (CV on Full Model)
        methods = ["temperature", "platt", "isotonic"]
        all_cal_results: list[CalibrationMethodResult] = []

        baseline_metrics = self._compute_metrics(full_probs, full_actuals)
        all_cal_results.append(CalibrationMethodResult(
            method_name="none (uncalibrated)",
            brier_score=baseline_metrics["brier"],
            log_loss=baseline_metrics["log_loss"],
            accuracy=baseline_metrics["accuracy"],
            ece=baseline_metrics["ece"],
            parameters={},
        ))

        for method in methods:
            try:
                cal_probs, params = ProbabilisticCalibrator.calibrate_cv(full_probs, full_actuals, method)
                metrics = self._compute_metrics(cal_probs, full_actuals)
                all_cal_results.append(CalibrationMethodResult(
                    method_name=method,
                    brier_score=metrics["brier"],
                    log_loss=metrics["log_loss"],
                    accuracy=metrics["accuracy"],
                    ece=metrics["ece"],
                    parameters=params,
                ))
            except Exception as e:
                logger.warning(f"Calibration method '{method}' failed: {e}")

        report.calibration_methods = all_cal_results

        # Best method by ECE (calibration quality)
        best = min(all_cal_results, key=lambda r: r.ece)
        report.best_method = best.method_name

        # 4. Benchmark before (5 models)
        for model_name in ["elo", "poisson", "dixon_coles", "full"]:
            md = models_data.get(model_name)
            if md is None:
                continue
            m = self._compute_metrics(md["probs"], md["actuals"])
            report.benchmark_before[model_name] = {
                "brier_score": m["brier"],
                "log_loss": m["log_loss"],
                "accuracy": m["accuracy"],
                "ece": m["ece"],
            }

        # 5. Benchmark after: calibrate each model with best non-none method
        non_none_methods = [r for r in all_cal_results if r.method_name != "none (uncalibrated)"]
        best_cal_method = min(non_none_methods, key=lambda r: r.ece).method_name if non_none_methods else "none"
        for model_name in ["poisson", "dixon_coles", "full"]:
            md = models_data.get(model_name)
            if md is None:
                continue
            if best_cal_method != "none":
                try:
                    cal_probs, _ = ProbabilisticCalibrator.calibrate_cv(
                        md["probs"], md["actuals"], best_cal_method
                    )
                    m = self._compute_metrics(cal_probs, md["actuals"])
                except Exception:
                    m = self._compute_metrics(md["probs"], md["actuals"])
            else:
                m = self._compute_metrics(md["probs"], md["actuals"])
            report.benchmark_after[model_name] = {
                "brier_score": m["brier"],
                "log_loss": m["log_loss"],
                "accuracy": m["accuracy"],
                "ece": m["ece"],
            }

        # Add Elo to benchmark_after too (uncalibrated)
        if "elo" in models_data:
            md = models_data["elo"]
            m = self._compute_metrics(md["probs"], md["actuals"])
            report.benchmark_after["elo"] = {
                "brier_score": m["brier"],
                "log_loss": m["log_loss"],
                "accuracy": m["accuracy"],
                "ece": m["ece"],
            }

        # 6. Bias reduction validation
        report.bias_reductions = BiasValidator.find_best_adjustments(matches)

        # 7. Recommendation
        report.recommendation = self._generate_recommendation(report)

        return report

    def _generate_all_predictions(
        self, matches: list[HistoricalMatchData], home_advantage: bool,
    ) -> dict:
        """Generate predictions for all 4 models + Elo baseline."""
        models_data: dict = {}

        for model_type in ["elo", "poisson", "dixon_coles", "full"]:
            predictions, actuals, _, _, _, _, _ = self.cal_engine._run_predictions(
                matches, home_advantage, model_type
            )
            probs = np.array([(p.home_win_prob, p.draw_prob, p.away_win_prob) for p in predictions])
            actuals_arr = np.array(actuals)
            models_data[model_type] = {"probs": probs, "actuals": actuals_arr}

        return models_data

    @staticmethod
    def _compute_metrics(pred_probs: np.ndarray, actuals: np.ndarray) -> dict:
        n = pred_probs.shape[0]
        if n == 0:
            return {"brier": 0, "log_loss": 0, "accuracy": 0, "ece": 0}

        brier = float(np.mean(np.sum((pred_probs - actuals) ** 2, axis=1)))
        eps = 1e-15
        clipped = np.clip(pred_probs, eps, 1 - eps)
        log_loss_val = float(-np.mean(np.sum(actuals * np.log(clipped), axis=1)))
        pred_class = np.argmax(pred_probs, axis=1)
        actual_class = np.argmax(actuals, axis=1)
        acc = float(np.mean(pred_class == actual_class))

        # ECE
        confidences = np.max(pred_probs, axis=1)
        correct = pred_class == actual_class
        ece = 0.0
        for i in range(10):
            lo, hi = i / 10.0, (i + 1) / 10.0
            in_bin = (confidences > lo) & (confidences <= hi)
            if np.any(in_bin):
                acc_bin = float(np.mean(correct[in_bin]))
                conf_bin = float(np.mean(confidences[in_bin]))
                ece += len(confidences[in_bin]) * abs(acc_bin - conf_bin)
        ece = ece / len(confidences) if len(confidences) > 0 else 0.0

        return {
            "brier": round(brier, 4),
            "log_loss": round(log_loss_val, 4),
            "accuracy": round(acc, 4),
            "ece": round(ece, 4),
        }

    @staticmethod
    def _generate_recommendation(report: RefinementReport) -> str:
        lines = []

        # Best calibration method
        best = report.best_method
        best_detail = next((m for m in report.calibration_methods if m.method_name == best), None)
        if best_detail:
            lines.append(
                f"Recommended calibration method: '{best}' "
                f"(Brier={best_detail.brier_score}, ECE={best_detail.ece})."
            )

        # Best model after calibration
        if report.benchmark_after:
            best_model = min(
                report.benchmark_after.items(),
                key=lambda kv: kv[1]["brier_score"],
            )
            lines.append(
                f"Best model after calibration: '{best_model[0]}' "
                f"(Brier={best_model[1]['brier_score']}, "
                f"Acc={best_model[1]['accuracy']}, "
                f"ECE={best_model[1]['ece']})."
            )

        # Bias reduction summary
        applied = [r for r in report.bias_reductions if r.applied]
        if applied:
            lines.append(
                f"Validated bias reductions ({len(applied)}): "
                + ", ".join(f"{r.adjustment_name}={r.after_metric:.4f}" for r in applied[:3])
                + "."
            )
        else:
            lines.append("No bias adjustments validated (none improved Brier score).")

        return " ".join(lines)
