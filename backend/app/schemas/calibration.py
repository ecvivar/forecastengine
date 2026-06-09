from pydantic import BaseModel, ConfigDict


class CalibrationBinResponse(BaseModel):
    bin_lower: float
    bin_upper: float
    count: int
    mean_predicted: float
    mean_actual: float


class CalibrationMetricResponse(BaseModel):
    brier_score: float
    log_loss: float
    accuracy: float
    calibration_error: float
    auc_roc: float = 0.0


class BiasReportResponse(BaseModel):
    home_bias: float
    favorite_bias: float
    draw_bias: float
    underdog_bias: float
    high_confidence_bias: float
    low_confidence_bias: float


class CalibrationReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    overall: CalibrationMetricResponse
    by_tournament: dict[str, CalibrationMetricResponse] = {}
    by_stage: dict[str, CalibrationMetricResponse] = {}
    calibration_curve: list[CalibrationBinResponse] = []
    bias: BiasReportResponse | None = None
    match_count: int = 0
    weight_adjustments: dict[str, float] = {}
