from __future__ import annotations
import json
import numpy as np
from pathlib import Path
from typing import Optional


SIM_PATH = Path("backend/data/recalibration_simulations.json")


class RecalibrationSimulator:
    def __init__(self, path: Path = SIM_PATH):
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

    def simulate(
        self,
        predictions: list[float],
        outcomes: list[float],
        schedule: str = "weekly",
        phases: Optional[list[int]] = None,
    ) -> dict:
        phases = phases or [1, 2, 3]

        if schedule == "weekly":
            return self._simulate_weekly(predictions, outcomes, phases)
        elif schedule == "by_phase":
            return self._simulate_by_phase(predictions, outcomes, phases)
        elif schedule == "cumulative":
            return self._simulate_cumulative(predictions, outcomes)
        return {}

    def _simulate_weekly(
        self,
        predictions: list[float],
        outcomes: list[float],
        phases: list[int],
    ) -> dict:
        n = len(predictions)
        week_size = max(n // 4, 1)
        results = []
        for week in range(1, 5):
            start = (week - 1) * week_size
            end = min(week * week_size, n)
            if end <= start:
                break
            preds = np.array(predictions[start:end])
            outs = np.array(outcomes[start:end])
            results.append(self._compute_metrics(preds, outs, f"week_{week}"))
        self._save(results, "weekly")
        return {"schedule": "weekly", "phases": results}

    def _simulate_by_phase(
        self,
        predictions: list[float],
        outcomes: list[float],
        phases: list[int],
    ) -> dict:
        n = len(predictions)
        phase_size = max(n // len(phases), 1)
        results = []
        for phase in phases:
            start = (phase - 1) * phase_size
            end = min(phase * phase_size, n)
            if end <= start:
                break
            preds = np.array(predictions[start:end])
            outs = np.array(outcomes[start:end])
            results.append(self._compute_metrics(preds, outs, f"phase_{phase}"))
        self._save(results, "by_phase")
        return {"schedule": "by_phase", "phases": results}

    def _simulate_cumulative(
        self,
        predictions: list[float],
        outcomes: list[float],
    ) -> dict:
        n = len(predictions)
        steps = min(n, 5)
        step_size = max(n // steps, 1)
        results = []
        for i in range(1, steps + 1):
            end = min(i * step_size, n)
            preds = np.array(predictions[:end])
            outs = np.array(outcomes[:end])
            results.append(self._compute_metrics(preds, outs, f"step_{i}"))
        self._save(results, "cumulative")
        return {"schedule": "cumulative", "phases": results, "final": results[-1] if results else {}}

    def _compute_metrics(self, preds: np.ndarray, outs: np.ndarray, label: str) -> dict:
        ece = self._ece(preds, outs)
        brier = float(np.mean((preds - outs) ** 2))
        coverage = self._coverage(preds, outs)
        return {
            "phase": label,
            "n": len(preds),
            "ece": round(ece, 6),
            "brier": round(brier, 6),
            "coverage": round(coverage, 6),
            "accuracy": round(float(np.mean((preds >= 0.5) == outs.astype(bool))), 6),
        }

    def _ece(self, preds: np.ndarray, outcomes: np.ndarray, n_bins: int = 10) -> float:
        bins = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        for i in range(n_bins):
            mask = (preds >= bins[i]) & (preds < bins[i + 1])
            if not mask.any():
                continue
            ece += (mask.sum() / len(preds)) * abs(outcomes[mask].mean() - preds[mask].mean())
        return float(ece)

    def _coverage(self, preds: np.ndarray, outcomes: np.ndarray) -> float:
        low = np.clip(preds - 0.1, 0, 1)
        high = np.clip(preds + 0.1, 0, 1)
        return float(((outcomes >= low) & (outcomes <= high)).mean())

    def _save(self, results: list[dict], schedule: str):
        tracker = self._read()
        tracker.append({
            "timestamp": np.datetime64("now").item().isoformat() if hasattr(np.datetime64("now"), "item") else str(np.datetime64("now")),
            "schedule": schedule,
            "results": results,
        })
        self._write(tracker)

    def get_history(self) -> list[dict]:
        return self._read()

    def clear(self):
        self._write([])
