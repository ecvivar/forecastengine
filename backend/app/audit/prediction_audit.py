import json
import hashlib
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


AUDIT_LOG = Path("backend/data/prediction_audit_log.csv")


class PredictionAudit:
    def __init__(self, log_path: Path = AUDIT_LOG):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        competition_id: str,
        home_team: str,
        away_team: str,
        probabilities: dict,
        calibration_version: str = "1.0",
        model_version: str = "ensemble_v4",
        config_hash: Optional[str] = None,
        ensemble_weights: Optional[dict] = None,
        ci: Optional[tuple] = None,
        uncertainty_metrics: Optional[dict] = None,
        trigger: str = "api",
    ):
        config_str = json.dumps({
            "calibration_version": calibration_version,
            "model_version": model_version,
        }, sort_keys=True)
        if config_hash is None:
            config_hash = hashlib.sha256(config_str.encode()).hexdigest()[:12]

        probs = {"home": 0.0, "draw": 0.0, "away": 0.0}
        if probabilities:
            probs.update({k: round(v, 6) for k, v in probabilities.items()})

        ens_json = ""
        if ensemble_weights:
            ens_json = json.dumps({k: round(v, 4) for k, v in ensemble_weights.items()}, sort_keys=True)

        self._ensure_header()
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "competition_id": competition_id,
            "home_team": home_team,
            "away_team": away_team,
            "prob_home": probs.get("home", 0.0),
            "prob_draw": probs.get("draw", 0.0),
            "prob_away": probs.get("away", 0.0),
            "calibration_version": calibration_version,
            "model_version": model_version,
            "config_hash": config_hash,
            "ensemble_weights": ens_json,
            "ci_lower": round(ci[0], 6) if ci else "",
            "ci_upper": round(ci[1], 6) if ci else "",
            "uncertainty_spread": round(uncertainty_metrics.get("spread", 0), 6) if uncertainty_metrics else "",
            "uncertainty_entropy": round(uncertainty_metrics.get("entropy", 0), 6) if uncertainty_metrics else "",
            "uncertainty_bootstrap_var": round(uncertainty_metrics.get("bootstrap_variance", 0), 6) if uncertainty_metrics else "",
            "trigger": trigger,
        }
        with open(self.log_path, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(row.keys()))
            w.writerow(row)

    def get_history(
        self,
        team: Optional[str] = None,
        competition: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        results = []
        with open(self.log_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if team and team.lower() not in (row["home_team"].lower(), row["away_team"].lower()):
                    continue
                if competition and row["competition_id"] != competition:
                    continue
                results.append(row)
        return results[-limit:]

    def count(self) -> int:
        with open(self.log_path, "r") as f:
            return sum(1 for _ in f) - 1

    def get_teams(self) -> set:
        teams = set()
        with open(self.log_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                teams.add(row["home_team"])
                teams.add(row["away_team"])
        return teams

    def _ensure_header(self):
        if not self.log_path.exists():
            with open(self.log_path, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow([
                    "timestamp", "competition_id", "home_team", "away_team",
                    "prob_home", "prob_draw", "prob_away",
                    "calibration_version", "model_version", "config_hash",
                    "ensemble_weights", "ci_lower", "ci_upper",
                    "uncertainty_spread", "uncertainty_entropy",
                    "uncertainty_bootstrap_var", "trigger",
                ])

    def clear(self):
        if self.log_path.exists():
            self.log_path.unlink()
