from __future__ import annotations
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional


REGISTRY_PATH = Path("backend/data/model_registry.json")


class ModelRegistry:
    def __init__(self, path: Path = REGISTRY_PATH):
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

    def register(
        self,
        sprint_version: str,
        config_version: str,
        calibration_version: str,
        ensemble_version: str,
        description: str = "",
        metadata: Optional[dict] = None,
    ) -> dict:
        entry = {
            "id": hashlib.sha256(
                f"{sprint_version}_{config_version}_{calibration_version}_{ensemble_version}_{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()[:12],
            "sprint_version": sprint_version,
            "config_version": config_version,
            "calibration_version": calibration_version,
            "ensemble_version": ensemble_version,
            "description": description,
            "active": False,
            "registered_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        registry = self._read()
        for existing in registry:
            existing["active"] = False
        entry["active"] = True
        registry.append(entry)
        self._write(registry)
        return entry

    def get_active_model(self) -> Optional[dict]:
        registry = self._read()
        for entry in reversed(registry):
            if entry["active"]:
                return entry
        return registry[-1] if registry else None

    def get_model_history(self, limit: int = 50) -> list[dict]:
        registry = self._read()
        return registry[-limit:]

    def deactivate(self, model_id: str) -> bool:
        registry = self._read()
        for entry in registry:
            if entry["id"] == model_id:
                entry["active"] = False
                self._write(registry)
                return True
        return False

    def activate(self, model_id: str) -> bool:
        registry = self._read()
        for entry in registry:
            entry["active"] = entry["id"] == model_id
        self._write(registry)
        return True

    def count(self) -> int:
        return len(self._read())

    def get_model(self, model_id: str) -> Optional[dict]:
        registry = self._read()
        for entry in registry:
            if entry["id"] == model_id:
                return entry
        return None

    def clear(self):
        self._write([])
