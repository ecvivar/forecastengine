from pydantic import BaseModel


class ProbabilityBucketResponse(BaseModel):
    bucket_label: str
    lower: float
    upper: float
    count: int
    mean_predicted: float
    observed_frequency: float
    absolute_error: float
    relative_error: float


class ReliabilityCurveResponse(BaseModel):
    outcome: str
    buckets: list[ProbabilityBucketResponse] = []


class CalibrationMethodResultResponse(BaseModel):
    method_name: str
    brier_score: float
    log_loss: float
    accuracy: float
    ece: float
    parameters: dict = {}


class BiasReductionResultResponse(BaseModel):
    adjustment_name: str
    before_metric: float
    after_metric: float
    improvement: float
    applied: bool


class ModelMetricsResponse(BaseModel):
    brier_score: float
    log_loss: float
    accuracy: float
    ece: float


class RefinementReportResponse(BaseModel):
    reliability_curves: list[ReliabilityCurveResponse] = []
    calibration_methods: list[CalibrationMethodResultResponse] = []
    best_method: str = ""
    benchmark_before: dict[str, ModelMetricsResponse] = {}
    benchmark_after: dict[str, ModelMetricsResponse] = {}
    bias_reductions: list[BiasReductionResultResponse] = []
    recommendation: str = ""
