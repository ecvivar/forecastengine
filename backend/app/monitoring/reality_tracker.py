from __future__ import annotations
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional


REALITY_PATH = Path("backend/data/reality_tracker.json")


class RealityTracker:
    def __init__(self, path: Path = REALITY_PATH):
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

    def record(
        self,
        home_team: str,
        away_team: str,
        home_pred: float,
        draw_pred: float,
        away_pred: float,
        home_score: int,
        away_score: int,
        competition: str = "world_cup_2026",
        metadata: Optional[dict] = None,
    ) -> dict:
        if home_score > away_score:
            outcome = "home"
        elif away_score > home_score:
            outcome = "away"
        else:
            outcome = "draw"

        pred_probs = {"home": home_pred, "draw": draw_pred, "away": away_pred}
        pred_outcome = max(pred_probs, key=pred_probs.get)
        correct = pred_outcome == outcome

        surprise = 1.0 - pred_probs.get(outcome, 0.0)
        upset_index = self._compute_upset(home_pred, away_pred, home_score, away_score)

        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "competition": competition,
            "home_team": home_team,
            "away_team": away_team,
            "home_pred": round(home_pred, 6),
            "draw_pred": round(draw_pred, 6),
            "away_pred": round(away_pred, 6),
            "home_score": home_score,
            "away_score": away_score,
            "outcome": outcome,
            "predicted_outcome": pred_outcome,
            "correct": correct,
            "surprise_score": round(surprise, 6),
            "upset_index": round(upset_index, 6),
            "metadata": metadata or {},
        }
        tracker = self._read()
        tracker.append(entry)
        self._write(tracker)
        return entry

    def _compute_upset(self, home_pred: float, away_pred: float, home_score: int, away_score: int) -> float:
        if home_score > away_score:
            return float(max(0, 0.5 - home_pred) * 2)
        elif away_score > home_score:
            return float(max(0, 0.5 - away_pred) * 2)
        return 0.0

    def get_recent(self, limit: int = 20) -> list[dict]:
        return self._read()[-limit:]

    def get_surprise_matches(self, min_surprise: float = 0.3) -> list[dict]:
        return [m for m in self._read() if m["surprise_score"] >= min_surprise]

    def get_upset_matches(self, min_upset: float = 0.3) -> list[dict]:
        return [m for m in self._read() if m["upset_index"] >= min_upset]

    def get_accuracy(self) -> float:
        entries = self._read()
        if not entries:
            return 0.0
        return sum(1 for e in entries if e["correct"]) / len(entries)

    def get_calibration_impact(self) -> dict:
        entries = self._read()
        if not entries:
            return {}
        brier = np.mean([(1.0 - {"home": e["home_pred"], "draw": e["draw_pred"], "away": e["away_pred"]}.get(e["outcome"], 0)) ** 2 for e in entries])
        accuracy = sum(1 for e in entries if e["correct"]) / len(entries)
        return {"accuracy": round(accuracy, 4), "brier": round(float(brier), 6), "n": len(entries)}

    def get_team_summary(self, team: str) -> dict:
        entries = [e for e in self._read() if team.lower() in (e["home_team"].lower(), e["away_team"].lower())]
        if not entries:
            return {"team": team, "matches": 0}
        return {
            "team": team,
            "matches": len(entries),
            "accuracy": round(sum(1 for e in entries if e["correct"]) / len(entries), 4),
            "avg_surprise": round(np.mean([e["surprise_score"] for e in entries]), 6),
            "avg_upset": round(np.mean([e["upset_index"] for e in entries]), 6),
        }

    def clear(self):
        self._write([])
