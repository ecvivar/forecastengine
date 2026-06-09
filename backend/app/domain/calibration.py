from dataclasses import dataclass, field
from enum import Enum


class CalibrationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CalibrationMetric:
    brier_score: float
    log_loss: float
    accuracy: float
    calibration_error: float
    auc_roc: float = 0.0
    n_matches: int = 0


@dataclass
class CalibrationBin:
    bin_lower: float
    bin_upper: float
    count: int
    mean_predicted: float
    mean_actual: float


@dataclass
class BiasReport:
    home_bias: float
    favorite_bias: float
    draw_bias: float
    underdog_bias: float
    high_confidence_bias: float
    low_confidence_bias: float


@dataclass
class ConfederationBias:
    confederation: str
    match_count: int
    brier_score: float
    accuracy: float
    home_win_pred: float
    home_win_actual: float
    favorite_pred: float
    favorite_actual: float
    draw_pred: float
    draw_actual: float


@dataclass
class FavoriteBias:
    bracket_lower: float
    bracket_upper: float
    count: int
    mean_predicted_prob: float
    mean_actual_win_rate: float


@dataclass
class DrawBias:
    match_count: int
    predicted_draw_rate: float
    actual_draw_rate: float
    bias: float


@dataclass
class HomeBias:
    match_count: int
    predicted_home_win_rate: float
    actual_home_win_rate: float
    bias: float


@dataclass
class OutcomeCalibrationCurve:
    outcome: str  # "home", "draw", "away"
    bins: list[CalibrationBin] = field(default_factory=list)


@dataclass
class ModelComparisonResult:
    model_name: str
    overall: CalibrationMetric
    by_tournament: dict[str, CalibrationMetric] = field(default_factory=dict)
    by_stage: dict[str, CalibrationMetric] = field(default_factory=dict)


@dataclass
class BenchmarkReport:
    models: list[ModelComparisonResult] = field(default_factory=list)
    best_model: str = ""
    improvement_vs_baseline: dict[str, float] = field(default_factory=dict)


@dataclass
class CalibrationReport:
    status: CalibrationStatus
    overall: CalibrationMetric
    by_tournament: dict[str, CalibrationMetric] = field(default_factory=dict)
    by_stage: dict[str, CalibrationMetric] = field(default_factory=dict)
    calibration_curve: list[CalibrationBin] = field(default_factory=list)
    outcome_curves: list[OutcomeCalibrationCurve] = field(default_factory=list)
    bias: BiasReport | None = None
    confederation_biases: list[ConfederationBias] = field(default_factory=list)
    favorite_biases: list[FavoriteBias] = field(default_factory=list)
    draw_bias_detail: DrawBias | None = None
    home_bias_detail: HomeBias | None = None
    match_count: int = 0
    weight_adjustments: dict[str, float] = field(default_factory=dict)
    benchmark: BenchmarkReport | None = None


@dataclass
class HistoricalMatchData:
    tournament: str
    stage: str
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    home_elo: int
    away_elo: int
    home_igf: float
    away_igf: float
    home_penalties: int | None = None
    away_penalties: int | None = None
    home_confederation: str = ""
    away_confederation: str = ""
