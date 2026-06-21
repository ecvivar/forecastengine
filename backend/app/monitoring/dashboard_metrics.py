from __future__ import annotations
import json
import numpy as np
from pathlib import Path
from typing import Optional


DASHBOARD_PATH = Path("backend/data/dashboard_metrics.json")


class DashboardMetrics:
    def __init__(self, path: Path = DASHBOARD_PATH):
        self.path = path

    def compute(
        self,
        teams: list[str],
        elos: Optional[dict[str, float]] = None,
        champion_probs: Optional[dict[str, float]] = None,
        prediction_history: Optional[list[dict]] = None,
        uncertainty_scores: Optional[dict[str, float]] = None,
    ) -> dict:
        elos = elos or {}
        champion_probs = champion_probs or {}
        uncertainty_scores = uncertainty_scores or {}

        sorted_elos = sorted(elos.items(), key=lambda x: x[1], reverse=True)
        sorted_champs = sorted(champion_probs.items(), key=lambda x: x[1], reverse=True)
        sorted_uncertainty = sorted(uncertainty_scores.items(), key=lambda x: x[1], reverse=True)

        movers = self._compute_movers(prediction_history) if prediction_history else []

        result = {
            "top_contenders": [
                {"team": t, "elo": round(e, 1)}
                for t, e in sorted_elos[:10]
            ],
            "champion_probabilities": [
                {"team": t, "prob": round(p, 4)}
                for t, p in sorted_champs[:10]
            ],
            "biggest_movers": movers[:5],
            "most_uncertain_teams": [
                {"team": t, "uncertainty": round(u, 4)}
                for t, u in sorted_uncertainty[-5:]
            ],
            "most_stable_teams": [
                {"team": t, "stability": round(1 - u, 4)}
                for t, u in sorted_uncertainty[:5]
            ],
            "calibration_status": self._get_calibration_status(),
        }
        self._save(result)
        return result

    def _compute_movers(self, history: list[dict]) -> list[dict]:
        if len(history) < 2:
            return []
        recent = history[-1].get("elos", {})
        previous = history[-2].get("elos", {})
        movers = []
        for team in recent:
            diff = recent.get(team, 1500) - previous.get(team, 1500)
            movers.append({"team": team, "elo_change": round(diff, 1)})
        movers.sort(key=lambda x: abs(x["elo_change"]), reverse=True)
        return movers

    def _get_calibration_status(self) -> dict:
        try:
            from app.monitoring.calibration_tracker import CalibrationTracker
            tracker = CalibrationTracker()
            return tracker.get_status()
        except Exception:
            return {"status": "unavailable"}

    def _save(self, data: dict):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self) -> dict:
        if self.path.exists():
            with open(self.path, "r") as f:
                return json.load(f)
        return {}
