from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel

from app.schemas.calibration import CalibrationReportResponse
from app.services.calibration_service import CalibrationService

router = APIRouter(prefix="/calibration", tags=["Calibration"])

_service: CalibrationService | None = None


def get_service() -> CalibrationService:
    global _service
    if _service is None:
        _service = CalibrationService()
    return _service


@router.post("/run", response_model=CalibrationReportResponse)
def run_calibration(
    tournaments: list[str] | None = Query(None, description="Filter by tournaments (e.g. 2014, 2018, 2022)"),
):
    """Run calibration against historical World Cup data (2014, 2018, 2022)."""
    try:
        return get_service().run_calibration(tournaments)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/results", response_model=CalibrationReportResponse)
def get_calibration_results():
    """Get last calibration results."""
    report = get_service().get_last_report()
    if not report:
        raise HTTPException(status_code=404, detail="No calibration results yet. POST /calibration/run first.")
    return report


class ApplyAdjustmentsRequest(BaseModel):
    adjustments: dict[str, float]


@router.post("/apply")
def apply_adjustments(body: ApplyAdjustmentsRequest):
    """Apply calibration adjustments to the prediction engine."""
    get_service().apply_adjustments(body.adjustments)
    return {"status": "applied", "adjustments": body.adjustments}


@router.get("/adjustments")
def get_active_adjustments():
    """Get currently active calibration adjustments."""
    return {"adjustments": get_service().get_active_adjustments()}
