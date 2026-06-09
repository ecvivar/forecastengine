import logging

from app.data.historical_matches import ALL_HISTORICAL_MATCHES
from app.engine.calibration import CalibrationEngine
from app.engine.match_prediction import MatchPredictionConfig
from app.schemas.calibration import (
    BiasReportResponse,
    CalibrationBinResponse,
    CalibrationMetricResponse,
    CalibrationReportResponse,
)

logger = logging.getLogger(__name__)

_active_adjustments: dict[str, float] = {}


class CalibrationService:
    def __init__(self, engine: CalibrationEngine | None = None):
        self.engine = engine or CalibrationEngine()
        self._last_report: CalibrationReportResponse | None = None

    def run_calibration(
        self, tournaments: list[str] | None = None,
    ) -> CalibrationReportResponse:
        matches = ALL_HISTORICAL_MATCHES
        if tournaments:
            matches = [m for m in matches if m.tournament in tournaments]
            if not matches:
                raise ValueError(f"No historical data for tournaments: {tournaments}")

        report = self.engine.calibrate(matches)

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
            overall=CalibrationMetricResponse(
                brier_score=report.overall.brier_score,
                log_loss=report.overall.log_loss,
                accuracy=report.overall.accuracy,
                calibration_error=report.overall.calibration_error,
                auc_roc=report.overall.auc_roc,
            ),
            by_tournament={
                k: CalibrationMetricResponse(
                    brier_score=v.brier_score,
                    log_loss=v.log_loss,
                    accuracy=v.accuracy,
                    calibration_error=v.calibration_error,
                    auc_roc=v.auc_roc,
                )
                for k, v in report.by_tournament.items()
            },
            by_stage={
                k: CalibrationMetricResponse(
                    brier_score=v.brier_score,
                    log_loss=v.log_loss,
                    accuracy=v.accuracy,
                    calibration_error=v.calibration_error,
                    auc_roc=v.auc_roc,
                )
                for k, v in report.by_stage.items()
            },
            calibration_curve=[
                CalibrationBinResponse(
                    bin_lower=b.bin_lower,
                    bin_upper=b.bin_upper,
                    count=b.count,
                    mean_predicted=b.mean_predicted,
                    mean_actual=b.mean_actual,
                )
                for b in report.calibration_curve
            ],
            bias=BiasReportResponse(
                home_bias=report.bias.home_bias,
                favorite_bias=report.bias.favorite_bias,
                draw_bias=report.bias.draw_bias,
                underdog_bias=report.bias.underdog_bias,
                high_confidence_bias=report.bias.high_confidence_bias,
                low_confidence_bias=report.bias.low_confidence_bias,
            ) if report.bias else None,
            match_count=report.match_count,
            weight_adjustments=report.weight_adjustments,
        )
