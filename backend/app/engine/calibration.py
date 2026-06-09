"""
Calibration Engine.

Validates the prediction model against historical World Cup data (2014, 2018, 2022).
Computes Brier Score, Log Loss, Accuracy, Calibration Error, AUC-ROC,
bias analysis, and suggests weight adjustments.
"""

import logging
import uuid
from collections import defaultdict
from typing import Callable

import numpy as np

from app.domain.calibration import (
    BiasReport,
    CalibrationBin,
    CalibrationMetric,
    CalibrationReport,
    CalibrationStatus,
    HistoricalMatchData,
)
from app.domain.entities import MatchPredictionResult, TeamEntity
from app.engine.match_prediction import MatchPredictionEngine

logger = logging.getLogger(__name__)

Outcome = tuple[int, int, int]  # one-hot: (home_win, draw, away_win)


class CalibrationEngine:
    """Validates prediction model against historical match data."""

    def __init__(
        self,
        prediction_engine: MatchPredictionEngine | None = None,
    ):
        self.prediction_engine = prediction_engine or MatchPredictionEngine()

    def calibrate(
        self,
        historical_matches: list[HistoricalMatchData],
        home_advantage: bool = False,
    ) -> CalibrationReport:
        """
        Run full calibration on historical matches.
        Returns a CalibrationReport with all metrics.
        """
        predictions: list[MatchPredictionResult] = []
        actuals: list[Outcome] = []
        tournaments: list[str] = []
        stages: list[str] = []
        confidences: list[float] = []

        for match in historical_matches:
            home_entity = TeamEntity(
                id=uuid.uuid4(),
                name=match.home_team,
                elo_score=match.home_elo,
                igf_score=match.home_igf,
            )
            away_entity = TeamEntity(
                id=uuid.uuid4(),
                name=match.away_team,
                elo_score=match.away_elo,
                igf_score=match.away_igf,
            )

            pred = self.prediction_engine.predict_full(
                home_entity, away_entity,
                home_advantage=home_advantage,
            )
            predictions.append(pred)
            actuals.append(self._outcome_onehot(match.home_goals, match.away_goals))
            tournaments.append(match.tournament)
            stages.append(match.stage)
            confidences.append(pred.confidence_index)

        n = len(predictions)
        if n == 0:
            return CalibrationReport(
                status=CalibrationStatus.FAILED,
                overall=CalibrationMetric(brier_score=0, log_loss=0, accuracy=0, calibration_error=0),
            )

        # Overall metrics
        pred_probs = np.array([(p.home_win_prob, p.draw_prob, p.away_win_prob) for p in predictions])
        actual_arr = np.array(actuals)
        overall = self._compute_metrics(pred_probs, actual_arr)

        # Per-tournament metrics
        by_tournament = {}
        for t in sorted(set(tournaments)):
            mask = [tournaments[i] == t for i in range(n)]
            if sum(mask) < 2:
                continue
            by_tournament[t] = self._compute_metrics(pred_probs[mask], actual_arr[mask])

        # Per-stage metrics
        by_stage = {}
        for s in sorted(set(stages)):
            mask = [stages[i] == s for i in range(n)]
            if sum(mask) < 2:
                continue
            by_stage[s] = self._compute_metrics(pred_probs[mask], actual_arr[mask])

        # Calibration curve
        curve = self._calibration_curve(pred_probs, actual_arr)

        # Bias analysis
        bias = self._bias_analysis(pred_probs, actual_arr, confidences)

        # Weight adjustment suggestions
        adjustments = self._suggest_adjustments(bias)

        return CalibrationReport(
            status=CalibrationStatus.COMPLETED,
            overall=overall,
            by_tournament=by_tournament,
            by_stage=by_stage,
            calibration_curve=curve,
            bias=bias,
            match_count=n,
            weight_adjustments=adjustments,
        )

    def _compute_metrics(
        self, pred_probs: np.ndarray, actuals: np.ndarray,
    ) -> CalibrationMetric:
        n = pred_probs.shape[0]
        if n == 0:
            return CalibrationMetric(brier_score=0, log_loss=0, accuracy=0, calibration_error=0)

        # Brier Score: mean squared error
        brier = float(np.mean(np.sum((pred_probs - actuals) ** 2, axis=1)))

        # Log Loss: -1/n * sum(y * log(p))
        eps = 1e-15
        clipped = np.clip(pred_probs, eps, 1 - eps)
        log_loss_val = float(-np.mean(np.sum(actuals * np.log(clipped), axis=1)))

        # Accuracy: predicted class matches actual
        pred_class = np.argmax(pred_probs, axis=1)
        actual_class = np.argmax(actuals, axis=1)
        acc = float(np.mean(pred_class == actual_class))

        # Calibration Error: ECE (Expected Calibration Error)
        cal_error = self._expected_calibration_error(pred_probs, actuals)

        # AUC-ROC (one-vs-rest for multiclass)
        auc = self._compute_auc_roc(pred_probs, actuals)

        return CalibrationMetric(
            brier_score=round(brier, 4),
            log_loss=round(log_loss_val, 4),
            accuracy=round(acc, 4),
            calibration_error=round(cal_error, 4),
            auc_roc=round(auc, 4),
        )

    @staticmethod
    def _compute_auc_roc(pred_probs: np.ndarray, actuals: np.ndarray) -> float:
        n_classes = pred_probs.shape[1]
        aucs = []
        for c in range(n_classes):
            y_true = actuals[:, c]
            y_score = pred_probs[:, c]
            order = np.argsort(y_score)[::-1]
            y_true_sorted = y_true[order]
            tpr, fpr = [0.0], [0.0]
            pos = float(np.sum(y_true_sorted))
            neg = float(len(y_true_sorted) - pos)
            if pos == 0 or neg == 0:
                continue
            tp, fp = 0.0, 0.0
            for v in y_true_sorted:
                if v == 1:
                    tp += 1
                else:
                    fp += 1
                tpr.append(tp / pos)
                fpr.append(fp / neg)
            auc_val = float(np.trapezoid(tpr, fpr))
            aucs.append(auc_val)
        return float(np.mean(aucs)) if aucs else 0.0

    @staticmethod
    def _expected_calibration_error(
        pred_probs: np.ndarray, actuals: np.ndarray, n_bins: int = 10,
    ) -> float:
        confidences = np.max(pred_probs, axis=1)
        correct = np.argmax(pred_probs, axis=1) == np.argmax(actuals, axis=1)

        bins = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        for i in range(n_bins):
            in_bin = (confidences > bins[i]) & (confidences <= bins[i + 1])
            if np.any(in_bin):
                acc_bin = float(np.mean(correct[in_bin]))
                conf_bin = float(np.mean(confidences[in_bin]))
                ece += len(confidences[in_bin]) * abs(acc_bin - conf_bin)

        return ece / len(confidences) if len(confidences) > 0 else 0.0

    @staticmethod
    def _calibration_curve(
        pred_probs: np.ndarray, actuals: np.ndarray, n_bins: int = 10,
    ) -> list[CalibrationBin]:
        confidences = np.max(pred_probs, axis=1)
        correct = np.argmax(pred_probs, axis=1) == np.argmax(actuals, axis=1)

        bins = np.linspace(0, 1, n_bins + 1)
        curve = []
        for i in range(n_bins):
            in_bin = (confidences > bins[i]) & (confidences <= bins[i + 1])
            count = int(np.sum(in_bin))
            if count > 0:
                curve.append(CalibrationBin(
                    bin_lower=round(bins[i], 2),
                    bin_upper=round(bins[i + 1], 2),
                    count=count,
                    mean_predicted=round(float(np.mean(confidences[in_bin])), 4),
                    mean_actual=round(float(np.mean(correct[in_bin])), 4),
                ))
        return curve

    @staticmethod
    def _bias_analysis(
        pred_probs: np.ndarray, actuals: np.ndarray, confidences: list[float],
    ) -> BiasReport:
        pred_class = np.argmax(pred_probs, axis=1)
        actual_class = np.argmax(actuals, axis=1)
        n = len(pred_class)

        if n == 0:
            return BiasReport(home_bias=0, favorite_bias=0, draw_bias=0, underdog_bias=0, high_confidence_bias=0, low_confidence_bias=0)

        # Home bias: did we predict home win more or less than actual?
        pred_home = np.mean(pred_class == 0)
        actual_home = np.mean(actual_class == 0)
        home_bias = round(float(pred_home - actual_home), 4)

        # Favorite bias: for matches with a clear favorite (prob > 0.5)
        favorite_mask = np.max(pred_probs, axis=1) > 0.5
        if np.any(favorite_mask):
            fav_correct = np.mean(pred_class[favorite_mask] == actual_class[favorite_mask])
        else:
            fav_correct = 0.0

        # Draw bias
        pred_draw = np.mean(pred_class == 1)
        actual_draw = np.mean(actual_class == 1)
        draw_bias = round(float(pred_draw - actual_draw), 4)

        # Underdog bias: when predicted probability for the winner is < 0.5
        underdog_pred = pred_probs[np.max(pred_probs, axis=1) < 0.5]
        underdog_actual = actuals[np.max(pred_probs, axis=1) < 0.5]
        if len(underdog_pred) > 0:
            underdog_rate = float(np.mean(np.argmax(underdog_pred, axis=1) == np.argmax(underdog_actual, axis=1)))
        else:
            underdog_rate = 0.0

        # Confidence-based bias
        conf_arr = np.array(confidences)
        high_mask = conf_arr > 65
        low_mask = conf_arr < 35
        high_bias = float(np.mean(pred_class[high_mask] == actual_class[high_mask])) if np.any(high_mask) else 0.0
        low_bias = float(np.mean(pred_class[low_mask] == actual_class[low_mask])) if np.any(low_mask) else 0.0

        return BiasReport(
            home_bias=home_bias,
            favorite_bias=round(float(fav_correct), 4),
            draw_bias=draw_bias,
            underdog_bias=round(underdog_rate, 4),
            high_confidence_bias=round(high_bias, 4),
            low_confidence_bias=round(low_bias, 4),
        )

    @staticmethod
    def _suggest_adjustments(bias: BiasReport) -> dict[str, float]:
        adjustments = {}
        # If we systematically over/under predict home advantage
        if abs(bias.home_bias) > 0.05:
            adjustments["home_advantage_adjustment"] = round(-bias.home_bias * 0.5, 4)
        # If favorite prediction is too confident
        if bias.favorite_bias < 0.5:
            adjustments["favorite_calibration_factor"] = 0.95
        # If draw prediction is biased (use 0.5 factor since draws are often underestimated)
        if abs(bias.draw_bias) > 0.03:
            adjustments["draw_adjustment"] = round(-bias.draw_bias * 0.5, 4)
        return adjustments

    @staticmethod
    def _outcome_onehot(home_goals: int, away_goals: int) -> Outcome:
        if home_goals > away_goals:
            return (1, 0, 0)
        elif home_goals == away_goals:
            return (0, 1, 0)
        return (0, 0, 1)
