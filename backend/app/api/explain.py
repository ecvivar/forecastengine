"""
Sprint 3 — FASE 6: Explainability API Endpoint.

GET /api/v1/matches/explain?home_team_id=...&away_team_id=...

Returns prediction + per-signal driver breakdown.
Reuses ExplainabilityEngine — no duplicated logic.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.domain.entities import PredictionConfig, TeamEntity
from app.engine.explainability import ExplainabilityEngine
from app.engine.match_prediction import MatchPredictionEngine
from app.models.elo_rating import EloRating
from app.models.fifa_ranking import FifaRanking
from app.models.team import Team
from app.models.xg_metrics import XGMetrics
from app.services.calibration_service import CalibrationService

router = APIRouter(prefix="/matches", tags=["Match Explainability"])


def _load_team_entity(db: Session, team_id: uuid.UUID) -> TeamEntity:
    """Load a TeamEntity from the database (same pattern as comparison.py)."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")

    latest_elo = (
        db.query(EloRating)
        .filter(EloRating.team_id == team_id)
        .order_by(EloRating.rating_date.desc())
        .first()
    )
    elo_score = latest_elo.elo_score if latest_elo else 1500

    latest_xg = (
        db.query(XGMetrics)
        .filter(XGMetrics.team_id == team_id)
        .order_by(XGMetrics.metric_date.desc())
        .first()
    )

    latest_fifa = (
        db.query(FifaRanking)
        .filter(FifaRanking.team_id == team_id)
        .order_by(FifaRanking.ranking_date.desc())
        .first()
    )

    return TeamEntity(
        id=team.id,
        name=team.name,
        fifa_code=team.fifa_code,
        continent=team.continent,
        elo_score=elo_score,
        fifa_rank=latest_fifa.rank if latest_fifa else 100,
        xg_for=latest_xg.xg_for if latest_xg else None,
        xg_against=latest_xg.xg_against if latest_xg else None,
    )


@router.get("/explain")
def explain_match(
    home_team_id: uuid.UUID = Query(..., description="Home team UUID"),
    away_team_id: uuid.UUID = Query(..., description="Away team UUID"),
    home_advantage: bool = Query(True, description="Give home advantage to home team"),
    db: Session = Depends(get_db),
):
    """
    Predict and explain a match between two teams.
    
    Returns prediction probabilities and per-signal driver breakdown.
    """
    home_entity = _load_team_entity(db, home_team_id)
    away_entity = _load_team_entity(db, away_team_id)

    cal_config = CalibrationService.build_config_with_adjustments()
    explainer = ExplainabilityEngine(config=cal_config)

    explanation = explainer.explain(home_entity, away_entity, home_advantage=home_advantage)
    return explanation.to_dict()
