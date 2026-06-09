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
class CalibrationReport:
    status: CalibrationStatus
    overall: CalibrationMetric
    by_tournament: dict[str, CalibrationMetric] = field(default_factory=dict)
    by_stage: dict[str, CalibrationMetric] = field(default_factory=dict)
    calibration_curve: list[CalibrationBin] = field(default_factory=list)
    bias: BiasReport | None = None
    match_count: int = 0
    weight_adjustments: dict[str, float] = field(default_factory=dict)


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
