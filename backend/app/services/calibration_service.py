import logging

from app.data.historical_matches import ALL_HISTORICAL_MATCHES
from app.engine.calibration import CalibrationEngine
from app.engine.match_prediction import MatchPredictionConfig
from app.schemas.calibration import (
    BenchmarkReportResponse,
    BiasReportResponse,
    CalibrationBinResponse,
    CalibrationMetricResponse,
    CalibrationReportResponse,
    ConfederationBiasResponse,
    DrawBiasResponse,
    FavoriteBiasResponse,
    HomeBiasResponse,
    ModelComparisonMetricResponse,
    OutcomeCalibrationCurveResponse,
)

logger = logging.getLogger(__name__)

_active_adjustments: dict[str, float] = {}


class CalibrationService:
    def __init__(self, engine: CalibrationEngine | None = None):
        self.engine = engine or CalibrationEngine()
        self._last_report: CalibrationReportResponse | None = None

    def run_calibration(
        self, tournaments: list[str] | None = None,
        model_type: str = "full",
    ) -> CalibrationReportResponse:
        matches = ALL_HISTORICAL_MATCHES
        if tournaments:
            matches = [m for m in matches if m.tournament in tournaments]
            if not matches:
                raise ValueError(f"No historical data for tournaments: {tournaments}")

        report = self.engine.calibrate(matches, home_advantage=False, model_type=model_type)
        response = self._to_response(report)
        self._last_report = response
        return response

    def run_benchmark(
        self, tournaments: list[str] | None = None,
    ) -> CalibrationReportResponse:
        matches = ALL_HISTORICAL_MATCHES
        if tournaments:
            matches = [m for m in matches if m.tournament in tournaments]
            if not matches:
                raise ValueError(f"No historical data for tournaments: {tournaments}")

        report = self.engine.benchmark(matches, home_advantage=False)
        response = self._to_response(report)
        self._last_report = response
        return response

    def get_last_report(self) -> CalibrationReportResponse | None:
        return self._last_report

    def apply_adjustments(self, adjustments: dict[str, float]) -> None:
        global _active_adjustments
        _active_adjustments = adjustments
        logger.info("Calibration adjustments applied: %s", adjustments)

    def get_active_adjustments(self) -> dict[str, float]:
        return dict(_active_adjustments)

    @staticmethod
    def build_config_with_adjustments() -> MatchPredictionConfig:
        return MatchPredictionConfig(
            calibration_adjustments=dict(_active_adjustments) if _active_adjustments else None,
        )

    def _to_response(self, report) -> CalibrationReportResponse:
        return CalibrationReportResponse(
            status=report.status.value,
            overall=self._metric_to_response(report.overall),
            by_tournament={k: self._metric_to_response(v) for k, v in report.by_tournament.items()},
            by_stage={k: self._metric_to_response(v) for k, v in report.by_stage.items()},
            calibration_curve=[
                CalibrationBinResponse(
                    bin_lower=b.bin_lower, bin_upper=b.bin_upper,
                    count=b.count, mean_predicted=b.mean_predicted, mean_actual=b.mean_actual,
                )
                for b in report.calibration_curve
            ],
            outcome_curves=[
                OutcomeCalibrationCurveResponse(
                    outcome=oc.outcome,
                    bins=[
                        CalibrationBinResponse(
                            bin_lower=b.bin_lower, bin_upper=b.bin_upper,
                            count=b.count, mean_predicted=b.mean_predicted, mean_actual=b.mean_actual,
                        )
                        for b in oc.bins
                    ],
                )
                for oc in report.outcome_curves
            ],
            bias=BiasReportResponse(
                home_bias=report.bias.home_bias, favorite_bias=report.bias.favorite_bias,
                draw_bias=report.bias.draw_bias, underdog_bias=report.bias.underdog_bias,
                high_confidence_bias=report.bias.high_confidence_bias,
                low_confidence_bias=report.bias.low_confidence_bias,
            ) if report.bias else None,
            confederation_biases=[
                ConfederationBiasResponse(
                    confederation=cb.confederation, match_count=cb.match_count,
                    brier_score=cb.brier_score, accuracy=cb.accuracy,
                    home_win_pred=cb.home_win_pred, home_win_actual=cb.home_win_actual,
                    favorite_pred=cb.favorite_pred, favorite_actual=cb.favorite_actual,
                    draw_pred=cb.draw_pred, draw_actual=cb.draw_actual,
                )
                for cb in report.confederation_biases
            ],
            favorite_biases=[
                FavoriteBiasResponse(
                    bracket_lower=fb.bracket_lower, bracket_upper=fb.bracket_upper,
                    count=fb.count, mean_predicted_prob=fb.mean_predicted_prob,
                    mean_actual_win_rate=fb.mean_actual_win_rate,
                )
                for fb in report.favorite_biases
            ],
            draw_bias_detail=DrawBiasResponse(
                match_count=report.draw_bias_detail.match_count,
                predicted_draw_rate=report.draw_bias_detail.predicted_draw_rate,
                actual_draw_rate=report.draw_bias_detail.actual_draw_rate,
                bias=report.draw_bias_detail.bias,
            ) if report.draw_bias_detail else None,
            home_bias_detail=HomeBiasResponse(
                match_count=report.home_bias_detail.match_count,
                predicted_home_win_rate=report.home_bias_detail.predicted_home_win_rate,
                actual_home_win_rate=report.home_bias_detail.actual_home_win_rate,
                bias=report.home_bias_detail.bias,
            ) if report.home_bias_detail else None,
            match_count=report.match_count,
            weight_adjustments=report.weight_adjustments,
            benchmark=self._benchmark_to_response(report.benchmark) if report.benchmark else None,
        )

    @staticmethod
    def _metric_to_response(m) -> CalibrationMetricResponse:
        return CalibrationMetricResponse(
            brier_score=m.brier_score, log_loss=m.log_loss,
            accuracy=m.accuracy, calibration_error=m.calibration_error,
            auc_roc=m.auc_roc, n_matches=m.n_matches,
        )

    @staticmethod
    def _benchmark_to_response(b) -> BenchmarkReportResponse:
        return BenchmarkReportResponse(
            models=[
                ModelComparisonMetricResponse(
                    model_name=m.model_name,
                    overall=CalibrationMetricResponse(
                        brier_score=m.overall.brier_score, log_loss=m.overall.log_loss,
                        accuracy=m.overall.accuracy, calibration_error=m.overall.calibration_error,
                        auc_roc=m.overall.auc_roc, n_matches=m.overall.n_matches,
                    ),
                    by_tournament={k: CalibrationMetricResponse(
                        brier_score=v.brier_score, log_loss=v.log_loss,
                        accuracy=v.accuracy, calibration_error=v.calibration_error,
                        auc_roc=v.auc_roc, n_matches=v.n_matches,
                    ) for k, v in m.by_tournament.items()},
                    by_stage={k: CalibrationMetricResponse(
                        brier_score=v.brier_score, log_loss=v.log_loss,
                        accuracy=v.accuracy, calibration_error=v.calibration_error,
                        auc_roc=v.auc_roc, n_matches=v.n_matches,
                    ) for k, v in m.by_stage.items()},
                )
                for m in b.models
            ],
            best_model=b.best_model,
            improvement_vs_baseline=b.improvement_vs_baseline,
        )
