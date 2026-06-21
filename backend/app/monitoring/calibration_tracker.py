from __future__ import annotations
import json
import numpy as np
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


TRACKER_PATH = Path("backend/data/calibration_tracker.json")


class CalibrationTracker:
    def __init__(self, path: Path = TRACKER_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])

    def _read(self) -> list[dict]:
        with open(self.path, "r") as f:
            return json.load(f)

    def _write(self, data: list[dict]):
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)

    def record_batch(
        self,
        predictions: list[float],
        outcomes: list[float],
        window: str = "day",
        tournament: str = "world_cup_2026",
    ):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "window": window,
            "tournament": tournament,
            "n": len(predictions),
            "accuracy": float(np.mean([(p >= 0.5) == bool(o) for p, o in zip(predictions, outcomes)])),
            "brier": float(np.mean([(p - o) ** 2 for p, o in zip(predictions, outcomes)])),
            "ece": self._compute_ece(np.array(predictions), np.array(outcomes)),
            "coverage": self._compute_coverage(np.array(predictions), np.array(outcomes)),
            "log_loss": float(np.mean([-o * np.log(max(p, 1e-15)) - (1 - o) * np.log(max(1 - p, 1e-15)) for p, o in zip(predictions, outcomes)])),
        }
        tracker = self._read()
        tracker.append(entry)
        self._write(tracker)

    def _compute_ece(self, preds: np.ndarray, outcomes: np.ndarray, n_bins: int = 10) -> float:
        bins = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        for i in range(n_bins):
            mask = (preds >= bins[i]) & (preds < bins[i + 1])
            if not mask.any():
                continue
            bin_acc = outcomes[mask].mean()
            bin_conf = preds[mask].mean()
            ece += (mask.sum() / len(preds)) * abs(bin_acc - bin_conf)
        return float(ece)

    def _compute_coverage(self, preds: np.ndarray, outcomes: np.ndarray) -> float:
        low = np.clip(preds - 0.1, 0, 1)
        high = np.clip(preds + 0.1, 0, 1)
        in_interval = ((outcomes >= low) & (outcomes <= high)).mean()
        return float(in_interval)

    def get_status(self, window: Optional[str] = None, tournament: Optional[str] = None) -> dict:
        tracker = self._read()
        if window:
            tracker = [e for e in tracker if e["window"] == window]
        if tournament:
            tracker = [e for e in tracker if e["tournament"] == tournament]
        if not tracker:
            return {}
        latest = tracker[-1]
        return {
            "accuracy": latest["accuracy"],
            "brier": latest["brier"],
            "ece": latest["ece"],
            "coverage": latest["coverage"],
            "log_loss": latest["log_loss"],
            "n": latest["n"],
            "timestamp": latest["timestamp"],
            "drift_warning": latest["ece"] > 0.045 or latest["brier"] > 0.22,
        }

    def get_daily_trend(self, days: int = 7) -> list[dict]:
        tracker = self._read()
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [
            e for e in tracker
            if datetime.fromisoformat(e["timestamp"]) >= cutoff
        ]

    def get_tournament_summary(self, tournament: str) -> dict:
        entries = [e for e in self._read() if e["tournament"] == tournament]
        if not entries:
            return {}
        return {
            "tournament": tournament,
            "entries": len(entries),
            "latest_brier": entries[-1]["brier"],
            "best_brier": min(e["brier"] for e in entries),
            "latest_ece": entries[-1]["ece"],
            "avg_ece": np.mean([e["ece"] for e in entries]),
            "latest_accuracy": entries[-1]["accuracy"],
        }

    def clear(self):
        self._write([])
