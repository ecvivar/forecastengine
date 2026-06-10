"""Phase 9.1 — Performance Benchmark Script."""

import json
import os
import sys
import time

sys.path.insert(0, ".")

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

os.environ["LOG_LEVEL"] = "WARNING"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from fastapi.testclient import TestClient

# Import all models so SQLAlchemy metadata registers properly with SQLite
from app.models import (  # noqa: F401
    competition,
    elo_rating,
    fifa_ranking,
    group,
    group_standing,
    match,
    player,
    simulation,
    team,
    xg_metrics,
)
from app.db.session import Base
from app.core.dependencies import get_db
from app.main import app
from app.engine.match_prediction import MatchPredictionConfig, MatchPredictionEngine
from app.engine.monte_carlo import run_single_tournament_py, MonteCarloEngine
from app.domain.entities import TeamEntity, SimulationConfig

# Set up SQLite engine and override DB dependency (like conftest.py)
_engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
Base.metadata.create_all(bind=_engine)

def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = _override_get_db

client = TestClient(app)

def measure(method: str, path: str, label: str, n: int = 5, json_body: dict | None = None) -> dict:
    latencies = []
    for _ in range(n):
        start = time.perf_counter()
        if json_body:
            resp = client.post(path, json=json_body)
        else:
            resp = client.get(path)
        elapsed = (time.perf_counter() - start) * 1000
        latencies.append(elapsed)
        resp.status_code
    latencies.sort()
    return {
        "label": label, "method": method, "path": path,
        "mean_ms": round(np.mean(latencies), 2),
        "p50_ms": round(np.median(latencies), 2),
        "p95_ms": round(latencies[int(len(latencies) * 0.95)], 2),
        "p99_ms": round(latencies[-1], 2),
        "min_ms": round(min(latencies), 2),
        "max_ms": round(max(latencies), 2),
        "samples": n,
    }

def measure_engine(label: str, fn, n: int = 5) -> dict:
    import tracemalloc
    latencies = []
    tracemalloc.start()
    for _ in range(n):
        start = time.perf_counter()
        fn()
        elapsed = (time.perf_counter() - start) * 1000
        latencies.append(elapsed)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    latencies.sort()
    return {
        "label": label,
        "mean_ms": round(np.mean(latencies), 2),
        "p50_ms": round(np.median(latencies), 2),
        "p95_ms": round(latencies[int(len(latencies) * 0.95)], 2),
        "max_ms": round(max(latencies), 2),
        "peak_memory_mb": round(peak / (1024 * 1024), 2),
        "samples": n,
    }

def main():
    results = {"api_endpoints": [], "engine_operations": []}

    # API Endpoints
    results["api_endpoints"].append(measure("GET", "/health", "Health Check"))
    results["api_endpoints"].append(measure("GET", "/api/v1/teams", "List Teams (empty DB)"))

    client.post("/api/v1/teams", json={"name": "Brazil", "fifa_code": "BRA", "continent": "South America"})
    client.post("/api/v1/teams", json={"name": "Argentina", "fifa_code": "ARG", "continent": "South America"})

    results["api_endpoints"].append(measure("GET", "/api/v1/teams", "List Teams"))
    results["api_endpoints"].append(measure("GET", "/api/v1/groups", "List Groups"))
    results["api_endpoints"].append(measure("GET", "/api/v1/rankings/igf", "IGF Rankings"))
    results["api_endpoints"].append(measure("GET", "/api/v1/dashboard", "Dashboard"))
    results["api_endpoints"].append(measure("GET", "/api/v1/export/matches/csv", "Export Matches CSV"))

    # Engine Operations
    teams = [
        TeamEntity(id=i, name=f"Team {i}", elo_score=1500 + (i % 5) * 100, igf_score=50.0 + (i % 10) * 5)
        for i in range(48)
    ]
    group_mapping = {t.id: chr(65 + (i % 12)) for i, t in enumerate(teams)}
    strengths = np.array([t.igf_score / 50.0 for t in teams], dtype=np.float64)
    assignments = np.array([ord(group_mapping[t.id]) - 65 for t in teams], dtype=np.int64)

    mp_engine = MatchPredictionEngine(config=MatchPredictionConfig())
    home, away = teams[0], teams[1]

    def predict_match():
        mp_engine.predict_full(home, away, home_advantage=True)

    results["engine_operations"].append(measure_engine("Single Match Prediction", predict_match))

    for n_sims, label in [(100, "MC 100 simulations"), (500, "MC 500 simulations"), (1000, "MC 1000 simulations")]:
        reps = n_sims // 100
        def mc_run(reps=reps):
            for _ in range(reps):
                run_single_tournament_py(strengths, assignments, 48)
        results["engine_operations"].append(measure_engine(label, mc_run, n=3 if n_sims > 100 else 5))

    # MC Engine (serial, 100 sims)
    mc_engine = MonteCarloEngine(config=SimulationConfig(num_simulations=100, parallel=False))
    def mc_engine_run():
        mc_engine.run(teams, group_mapping)

    results["engine_operations"].append(measure_engine("MC Engine 100 sims (serial)", mc_engine_run, n=3))

    print(json.dumps(results, indent=2))
    with open("audit/PERFORMANCE_BENCHMARK.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved to audit/PERFORMANCE_BENCHMARK.json")

if __name__ == "__main__":
    main()
