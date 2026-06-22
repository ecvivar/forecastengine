import csv
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.cache_decorator import cached
from app.core.dependencies import get_db
from app.audit.prediction_audit import AUDIT_LOG
from app.monitoring.drift_detector import DriftDetector
from app.monitoring.calibration_tracker import CalibrationTracker, TRACKER_PATH

router = APIRouter(prefix="/audit", tags=["Audit & Monitoring"])


@router.get("/log")
@cached("audit:log", ttl=30)
def get_audit_log(limit: int = Query(50, ge=1, le=500)):
    log_path = AUDIT_LOG
    if not log_path.exists():
        return []
    entries = []
    with open(log_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(row)
    return entries[-limit:]
