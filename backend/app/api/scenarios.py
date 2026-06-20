import uuid

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_db
from app.core.rate_limit import limiter
from app.engine.monte_carlo import run_single_tournament_py
from app.models.elo_rating import EloRating
from app.models.group import Group
from app.models.group_standing import GroupStanding
from app.models.simulation import Simulation, SimulationResult
from app.models.team import Team

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


class ScenarioModification(BaseModel):
    team_name: str
    result_modifier: float = 0.0
    forced_group_position: int | None = None
    description: str = ""


class ScenarioRequest(BaseModel):
    modifications: list[ScenarioModification]
    num_scenarios: int = 1000


class ScenarioResult(BaseModel):
    team_name: str
    win_prob: float
    final_prob: float
    sf_prob: float
    qf_prob: float
    r32_prob: float
    avg_group_points: float


@router.post("/simulate")
@limiter.limit("5/minute")
def simulate_scenario(request: Request, req: ScenarioRequest, db: Session = Depends(get_db)):
    teams = db.query(Team).order_by(Team.name).all()
    if not teams:
        raise HTTPException(status_code=400, detail="No teams in database")

    team_ids: list[uuid.UUID] = []
    team_names: list[str] = []
    strengths: list[float] = []
    group_names: list[str] = []

    mod_map = {m.team_name.lower(): m for m in req.modifications}

    all_team_ids = [team.id for team in teams]

    latest_elo_by_team = {}
    elo_rows = (
        db.query(EloRating)
        .filter(EloRating.team_id.in_(all_team_ids))
        .order_by(EloRating.team_id, EloRating.rating_date.desc())
        .all()
    )
    seen_elo = set()
    for r in elo_rows:
        if r.team_id not in seen_elo:
            latest_elo_by_team[r.team_id] = r.elo_score
            seen_elo.add(r.team_id)

    standing_by_team = {}
    standing_rows = (
        db.query(GroupStanding)
        .options(joinedload(GroupStanding.group))
        .filter(GroupStanding.team_id.in_(all_team_ids))
        .all()
    )
    for s in standing_rows:
        gname = s.group.name if s.group else "?"
        if s.team_id not in standing_by_team:
            standing_by_team[s.team_id] = gname

    for team in teams:
        team_ids.append(team.id)
        team_names.append(team.name)

        elo_score = latest_elo_by_team.get(team.id, 1500)
        igf = min(100, max(0, (elo_score - 1300) / 8))
        strength = igf / 50.0

        mod = mod_map.get(team.name.lower())
        if mod and mod.result_modifier != 0:
            strength *= (1 + mod.result_modifier / 100.0)

        strengths.append(strength)

        group_names.append(standing_by_team.get(team.id, "?"))

    unique_groups = sorted(set(group_names))
    group_to_idx = {g: i for i, g in enumerate(unique_groups)}
    assignments = np.array([group_to_idx[g] for g in group_names], dtype=np.int64)

    strengths_arr = np.array(strengths, dtype=np.float64)
    num_teams = len(teams)

    stage_counts = np.zeros((num_teams, 7), dtype=np.int32)

    for sim_idx in range(req.num_scenarios):
        sim_result = run_single_tournament_py(strengths_arr, assignments, num_teams)
        for t in range(num_teams):
            stage = sim_result[t, 0]
            if stage >= 1:
                stage_counts[t, 0] += 1
            if stage >= 2:
                stage_counts[t, 1] += 1
            if stage >= 3:
                stage_counts[t, 2] += 1
            if stage >= 4:
                stage_counts[t, 3] += 1
            if stage >= 5:
                stage_counts[t, 4] += 1
            if stage >= 6:
                stage_counts[t, 5] += 1
            stage_counts[t, 6] += sim_result[t, 2]  # accumulate group points

    n = max(req.num_scenarios, 1)
    results = []
    for i in range(num_teams):
        results.append({
            "team_name": team_names[i],
            "win_prob": round(stage_counts[i, 5] / n * 100, 1),
            "final_prob": round(stage_counts[i, 4] / n * 100, 1),
            "sf_prob": round(stage_counts[i, 3] / n * 100, 1),
            "qf_prob": round(stage_counts[i, 2] / n * 100, 1),
            "r32_prob": round(stage_counts[i, 0] / n * 100, 1),
            "avg_group_points": round(stage_counts[i, 6] / n, 2),
        })

    results.sort(key=lambda r: r["win_prob"], reverse=True)

    return {
        "scenario": {
            "num_scenarios": req.num_scenarios,
            "modifications": [
                {"team_name": m.team_name, "result_modifier": m.result_modifier, "description": m.description}
                for m in req.modifications
            ],
        },
        "results": results,
    }
