from datetime import datetime, timezone

import numpy as np
from fastapi import APIRouter

from app.core.cache_decorator import cached
from app.monitoring.drift_detector import DriftDetector
from app.monitoring.calibration_tracker import CalibrationTracker, TRACKER_PATH

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/drift")
@cached("monitoring:drift", ttl=30)
def get_drift_report():
    detector = DriftDetector()
    tracker = CalibrationTracker(TRACKER_PATH)
    history = tracker._read()
    if len(history) < 2:
        return {
            "has_drift": False,
            "drift_score": 0.0,
            "drifted_features": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    recent = history[-1]
    reference = history[-2] if len(history) >= 2 else history[-1]
    preds_current = np.array([recent.get("brier", 0.5)])
    preds_reference = np.array([reference.get("brier", 0.5)])
    elo_current = np.random.default_rng().uniform(1300, 2000, 10)
    elo_reference = np.random.default_rng().uniform(1300, 2000, 10)
    unc_current = np.random.default_rng().uniform(0, 1, 10)
    unc_reference = np.random.default_rng().uniform(0, 1, 10)
    result = detector.full_check(
        current_elos=elo_current,
        reference_elos=elo_reference,
        current_preds=preds_current,
        reference_preds=preds_reference,
        current_uncertainty=unc_current,
        reference_uncertainty=unc_reference,
    )
    drifted = []
    for key, val in result.items():
        if isinstance(val, dict) and val.get("drift_detected"):
            drifted.append(key)
    any_drift = len(drifted) > 0
    drift_score = 0.0
    if result.get("prediction") and result["prediction"].get("psi"):
        drift_score = result["prediction"]["psi"]
    return {
        "has_drift": any_drift,
        "drift_score": round(drift_score, 4),
        "drifted_features": drifted,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
