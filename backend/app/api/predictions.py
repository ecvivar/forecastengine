from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.cache_decorator import cached
from app.core.dependencies import PaginationParams, get_db
from app.core.rate_limit import limiter
from app.domain.entities import TeamEntity
from app.models.elo_rating import EloRating
from app.models.xg_metrics import XGMetrics
from app.schemas.match import MatchPrediction
from app.schemas.ranking import IGFScoreResponse
from app.services.match_service import MatchService
from app.services.ranking_service import RankingService

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.get("", response_model=list[MatchPrediction])
@cached("predictions:list")
@limiter.limit("10/minute")
def list_predictions(
    request: Request,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
):
    service = MatchService(db)
    matches = service.get_all(skip=pagination.offset, limit=pagination.limit)
    if not matches:
        return []

    team_ids = set()
    for m in matches:
        if m.home_team_id:
            team_ids.add(m.home_team_id)
        if m.away_team_id:
            team_ids.add(m.away_team_id)

    latest_elo_by_team = {}
    elo_rows = (
        db.query(EloRating)
        .filter(EloRating.team_id.in_(team_ids))
        .order_by(EloRating.team_id, EloRating.rating_date.desc())
        .all()
    )
    seen_elo = set()
    for r in elo_rows:
        if r.team_id not in seen_elo:
            latest_elo_by_team[r.team_id] = r.elo_score
            seen_elo.add(r.team_id)

    latest_xg_by_team = {}
    xg_rows = (
        db.query(XGMetrics)
        .filter(XGMetrics.team_id.in_(team_ids))
        .order_by(XGMetrics.team_id, XGMetrics.metric_date.desc())
        .all()
    )
    seen_xg = set()
    for r in xg_rows:
        if r.team_id not in seen_xg:
            latest_xg_by_team[r.team_id] = (r.xg_for, r.xg_against)
            seen_xg.add(r.team_id)

    def _make_entity(team):
        elo = latest_elo_by_team.get(team.id, 1500)
        xg = latest_xg_by_team.get(team.id, (1.0, 1.0))
        igf_strength = min(100.0, max(0.0, (elo - 1300) / 8))
        return TeamEntity(
            id=team.id, name=team.name, fifa_code=team.fifa_code,
            continent=team.continent, elo_score=elo, igf_score=igf_strength,
        )

    predictions = []
    for match in matches:
        if not match.home_team or not match.away_team:
            continue
        home_entity = _make_entity(match.home_team)
        away_entity = _make_entity(match.away_team)
        result = service.prediction_engine.predict_full(
            home_entity, away_entity, home_advantage=not match.is_neutral_venue,
        )
        predictions.append(MatchPrediction(
            match_id=match.id,
            home_team=match.home_team.name,
            away_team=match.away_team.name,
            home_win_prob=result.home_win_prob,
            draw_prob=result.draw_prob,
            away_win_prob=result.away_win_prob,
            home_expected_goals=result.home_expected_goals,
            away_expected_goals=result.away_expected_goals,
            most_likely_score=result.most_likely_score,
        ))
    return predictions


@router.get("/rankings", response_model=list[IGFScoreResponse])
@cached("predictions:rankings")
def get_igf_rankings(db: Session = Depends(get_db)):
    service = RankingService(db)
    return service.compute_igf()
