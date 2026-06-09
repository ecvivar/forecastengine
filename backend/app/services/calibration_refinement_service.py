import logging

from app.data.historical_matches import ALL_HISTORICAL_MATCHES
from app.engine.calibration_refinement import CalibrationRefinementEngine
from app.schemas.calibration_refinement import (
    BiasReductionResultResponse,
    CalibrationMethodResultResponse,
    ModelMetricsResponse,
    ProbabilityBucketResponse,
    RefinementReportResponse,
    ReliabilityCurveResponse,
)

logger = logging.getLogger(__name__)


class CalibrationRefinementService:
    def __init__(self):
        self._engine = CalibrationRefinementEngine()
        self._last_report: RefinementReportResponse | None = None

    def run_refinement(
        self, tournaments: list[str] | None = None,
    ) -> RefinementReportResponse:
        matches = ALL_HISTORICAL_MATCHES
        if tournaments:
            matches = [m for m in matches if m.tournament in tournaments]
            if not matches:
                raise ValueError(f"No historical data for tournaments: {tournaments}")

        report = self._engine.run_full_refinement(matches, home_advantage=False)
        response = self._to_response(report)
        self._last_report = response
        return response

    def get_last_report(self) -> RefinementReportResponse | None:
        return self._last_report

    @staticmethod
    def _to_response(report) -> RefinementReportResponse:
        return RefinementReportResponse(
            reliability_curves=[
                ReliabilityCurveResponse(
                    outcome=rc.outcome,
                    buckets=[
                        ProbabilityBucketResponse(
                            bucket_label=b.bucket_label, lower=b.lower, upper=b.upper,
                            count=b.count, mean_predicted=b.mean_predicted,
                            observed_frequency=b.observed_frequency,
                            absolute_error=b.absolute_error, relative_error=b.relative_error,
                        )
                        for b in rc.buckets
                    ],
                )
                for rc in report.reliability_curves
            ],
            calibration_methods=[
                CalibrationMethodResultResponse(
                    method_name=m.method_name, brier_score=m.brier_score,
                    log_loss=m.log_loss, accuracy=m.accuracy, ece=m.ece,
                    parameters=m.parameters,
                )
                for m in report.calibration_methods
            ],
            best_method=report.best_method,
            benchmark_before={
                k: ModelMetricsResponse(**v) for k, v in report.benchmark_before.items()
            },
            benchmark_after={
                k: ModelMetricsResponse(**v) for k, v in report.benchmark_after.items()
            },
            bias_reductions=[
                BiasReductionResultResponse(
                    adjustment_name=r.adjustment_name, before_metric=r.before_metric,
                    after_metric=r.after_metric, improvement=r.improvement,
                    applied=r.applied,
                )
                for r in report.bias_reductions
            ],
            recommendation=report.recommendation,
        )
