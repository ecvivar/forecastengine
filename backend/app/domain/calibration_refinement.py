from dataclasses import dataclass, field


@dataclass
class ProbabilityBucket:
    bucket_label: str
    lower: float
    upper: float
    count: int
    mean_predicted: float
    observed_frequency: float
    absolute_error: float
    relative_error: float


@dataclass
class ReliabilityCurve:
    outcome: str
    buckets: list[ProbabilityBucket] = field(default_factory=list)


@dataclass
class CalibrationMethodResult:
    method_name: str
    brier_score: float
    log_loss: float
    accuracy: float
    ece: float
    parameters: dict = field(default_factory=dict)


@dataclass
class BiasReductionResult:
    adjustment_name: str
    before_metric: float
    after_metric: float
    improvement: float
    applied: bool


@dataclass
class CalibratedModel:
    method_name: str
    fitted_params: dict  # serializable parameters for deployment


@dataclass
class RefinementReport:
    reliability_curves: list[ReliabilityCurve] = field(default_factory=list)
    calibration_methods: list[CalibrationMethodResult] = field(default_factory=list)
    best_method: str = ""
    benchmark_before: dict[str, dict] = field(default_factory=dict)
    benchmark_after: dict[str, dict] = field(default_factory=dict)
    bias_reductions: list[BiasReductionResult] = field(default_factory=list)
    recommendation: str = ""
