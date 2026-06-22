import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.core.cache_decorator import cached
from app.core.dependencies import get_db
from app.domain.entities import TeamEntity
from app.engine.insights import compute_insights
from app.engine.storytelling import (
    generate_headline,
    generate_story,
    generate_risks,
    generate_opportunities,
    generate_feed_events,
    generate_team_story,
)
from app.engine.match_prediction import MatchPredictionEngine
from app.engine.explainability import ExplainabilityEngine
from app.models.elo_rating import EloRating
from app.models.fifa_ranking import FifaRanking
from app.models.simulation import Simulation, SimulationResult
from app.models.team import Team
from app.models.xg_metrics import XGMetrics
from app.models.match import Match
from app.services.calibration_service import CalibrationService

router = APIRouter(prefix="/insights", tags=["Insights"])


def _load_team_entity(db: Session, team_id: uuid.UUID) -> TeamEntity:
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


def _load_team_data(db: Session, team_id: uuid.UUID) -> dict:
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
    igf_val = round(min(100, max(0, (elo_score - 1300) / 8)), 2)
    return {
        "team_id": str(team.id),
        "team_name": team.name,
        "fifa_code": team.fifa_code,
        "continent": team.continent,
        "flag_url": team.flag_url,
        "elo_score": elo_score,
        "igf_score": igf_val,
        "fifa_rank": latest_fifa.rank if latest_fifa else None,
        "xg_for": latest_xg.xg_for if latest_xg else None,
        "xg_against": latest_xg.xg_against if latest_xg else None,
    }


def _get_simulation_probs(db: Session) -> list[dict]:
    latest_sim = (
        db.query(Simulation)
        .filter(Simulation.status == "completed")
        .order_by(Simulation.completed_at.desc())
        .first()
    )
    if not latest_sim:
        return []
    results = (
        db.query(SimulationResult)
        .filter(SimulationResult.simulation_id == latest_sim.id)
        .all()
    )
    n = max(latest_sim.num_simulations, 1)
    teams_data = []
    for r in results:
        team = db.query(Team).filter(Team.id == r.team_id).first()
        if not team:
            continue
        latest_elo = (
            db.query(EloRating)
            .filter(EloRating.team_id == team.id)
            .order_by(EloRating.rating_date.desc())
            .first()
        )
        elo_score = latest_elo.elo_score if latest_elo else 1500
        teams_data.append({
            "team_name": team.name,
            "elo_score": elo_score,
            "win_prob": round(r.won_tournament / n * 100, 1),
            "final_prob": round(r.reached_final / n * 100, 1),
            "sf_prob": round(r.reached_semi_final / n * 100, 1),
            "qf_prob": round(r.reached_quarter_final / n * 100, 1),
        })
    teams_data.sort(key=lambda t: t["win_prob"], reverse=True)
    return teams_data


def _get_prev_simulation_probs(db: Session) -> list[dict]:
    sims = (
        db.query(Simulation)
        .filter(Simulation.status == "completed")
        .order_by(Simulation.completed_at.desc())
        .limit(2)
        .all()
    )
    if len(sims) < 2:
        return []
    prev = sims[-1]
    results = (
        db.query(SimulationResult)
        .filter(SimulationResult.simulation_id == prev.id)
        .all()
    )
    n = max(prev.num_simulations, 1)
    teams_data = []
    for r in results:
        team = db.query(Team).filter(Team.id == r.team_id).first()
        if not team:
            continue
        teams_data.append({
            "team_name": team.name,
            "win_prob": round(r.won_tournament / n * 100, 1),
            "final_prob": round(r.reached_final / n * 100, 1),
            "sf_prob": round(r.reached_semi_final / n * 100, 1),
            "qf_prob": round(r.reached_quarter_final / n * 100, 1),
        })
    teams_data.sort(key=lambda t: t["win_prob"], reverse=True)
    return teams_data


@router.get("/analysis")
@cached("insights:analysis", ttl=60)
def get_insights_analysis(db: Session = Depends(get_db)):
    teams = _get_simulation_probs(db)
    for t in teams:
        team_entity = db.query(Team).filter(Team.name == t["team_name"]).first()
        if team_entity:
            latest_fifa = (
                db.query(FifaRanking)
                .filter(FifaRanking.team_id == team_entity.id)
                .order_by(FifaRanking.ranking_date.desc())
                .first()
            )
            t["fifa_rank"] = latest_fifa.rank if latest_fifa else None
            latest_xg = (
                db.query(XGMetrics)
                .filter(XGMetrics.team_id == team_entity.id)
                .order_by(XGMetrics.metric_date.desc())
                .first()
            )
            t["xg_for"] = latest_xg.xg_for if latest_xg else None
            t["xg_against"] = latest_xg.xg_against if latest_xg else None
    insights = compute_insights(teams)
    return {"teams": teams, "insights": insights, "count": len(teams)}


@router.get("/narrative")
@cached("insights:narrative", ttl=60)
def get_narrative(db: Session = Depends(get_db)):
    teams = _get_simulation_probs(db)
    prev_teams = _get_prev_simulation_probs(db)
    for t in teams:
        team_entity = db.query(Team).filter(Team.name == t["team_name"]).first()
        if team_entity:
            latest_fifa = (
                db.query(FifaRanking)
                .filter(FifaRanking.team_id == team_entity.id)
                .order_by(FifaRanking.ranking_date.desc())
                .first()
            )
            t["fifa_rank"] = latest_fifa.rank if latest_fifa else None
            latest_xg = (
                db.query(XGMetrics)
                .filter(XGMetrics.team_id == team_entity.id)
                .order_by(XGMetrics.metric_date.desc())
                .first()
            )
            t["xg_for"] = latest_xg.xg_for if latest_xg else None
            t["xg_against"] = latest_xg.xg_against if latest_xg else None
    insights = compute_insights(teams)

    # Add surprise_risk to teams for story generation
    for t in teams[:20]:
        team_entity = db.query(Team).filter(Team.name == t["team_name"]).first()
        if team_entity:
            latest_elo = (
                db.query(EloRating)
                .filter(EloRating.team_id == team_entity.id)
                .order_by(EloRating.rating_date.desc())
                .first()
            )
            elo_score = latest_elo.elo_score if latest_elo else 1500
            t["elo_score"] = elo_score
            latest_xg = (
                db.query(XGMetrics)
                .filter(XGMetrics.team_id == team_entity.id)
                .order_by(XGMetrics.metric_date.desc())
                .first()
            )
            xg_for = latest_xg.xg_for if latest_xg else 1.2
            xg_against = latest_xg.xg_against if latest_xg else 1.2
            # simple surprise risk based on elo vs win prob disparity
            elo_norm = max(0, min(1, (elo_score - 1300) / 800))
            prob_norm = t["win_prob"] / 100
            t["surprise_risk"] = round(abs(elo_norm - prob_norm), 3)
            t["xg_for"] = xg_for
            t["xg_against"] = xg_against

    headline = generate_headline(insights)
    story = generate_story(teams, prev_teams)
    risks = generate_risks(insights, teams)
    opportunities = generate_opportunities(insights)
    feed = generate_feed_events(teams, prev_teams, insights)

    return {
        "headline": headline,
        "story": story,
        "risks": risks,
        "opportunities": opportunities,
        "news_feed": feed[:15],
    }


@router.get("/momentum")
@cached("insights:momentum", ttl=60)
def get_momentum(db: Session = Depends(get_db)):
    teams = _get_simulation_probs(db)
    prev_teams = _get_prev_simulation_probs(db)
    if not prev_teams:
        return {"momentum": [], "message": "Se necesita al menos dos simulaciones completadas para calcular momentum."}

    prev_map = {t["team_name"]: t for t in prev_teams}
    momentum = []
    for t in teams:
        if t["team_name"] in prev_map:
            p = prev_map[t["team_name"]]
            delta_w = round(t["win_prob"] - p["win_prob"], 1)
            delta_f = round(t["final_prob"] - p["final_prob"], 1)
            delta_sf = round(t["sf_prob"] - p["sf_prob"], 1)
            delta_qf = round(t["qf_prob"] - p["qf_prob"], 1)
            momentum.append({
                "team_name": t["team_name"],
                "win_prob": t["win_prob"],
                "prev_win_prob": p["win_prob"],
                "delta_win": delta_w,
                "delta_final": delta_f,
                "delta_sf": delta_sf,
                "delta_qf": delta_qf,
                "direction": "up" if delta_w > 0 else ("down" if delta_w < 0 else "stable"),
            })

    momentum.sort(key=lambda m: abs(m["delta_win"]), reverse=True)
    risers = [m for m in momentum if m["delta_win"] > 0][:8]
    fallers = [m for m in momentum if m["delta_win"] < 0][:8]

    return {
        "momentum": momentum,
        "risers": risers,
        "fallers": fallers,
    }


@router.get("/match-of-the-day")
@cached("insights:match-of-day", ttl=120)
def get_match_of_the_day(db: Session = Depends(get_db)):
    from app.engine.match_prediction import MatchPredictionEngine
    from app.domain.entities import TeamEntity

    latest_sim = (
        db.query(Simulation)
        .filter(Simulation.status == "completed")
        .order_by(Simulation.completed_at.desc())
        .first()
    )
    sim_results_map = {}
    if latest_sim:
        results = (
            db.query(SimulationResult)
            .filter(SimulationResult.simulation_id == latest_sim.id)
            .all()
        )
        n = max(latest_sim.num_simulations, 1)
        for r in results:
            team = db.query(Team).filter(Team.id == r.team_id).first()
            if team:
                sim_results_map[team.name] = r.won_tournament / n * 100

    upcoming = (
        db.query(Match)
        .filter(Match.status == "scheduled")
        .order_by(Match.match_date.asc())
        .limit(20)
        .all()
    )

    cal_config = CalibrationService.build_config_with_adjustments()
    engine = MatchPredictionEngine(config=cal_config)

    scored = []
    for m in upcoming:
        home_elo = (
            db.query(EloRating)
            .filter(EloRating.team_id == m.home_team_id)
            .order_by(EloRating.rating_date.desc())
            .first()
        )
        away_elo = (
            db.query(EloRating)
            .filter(EloRating.team_id == m.away_team_id)
            .order_by(EloRating.rating_date.desc())
            .first()
        )
        home_team = db.query(Team).filter(Team.id == m.home_team_id).first()
        away_team = db.query(Team).filter(Team.id == m.away_team_id).first()
        if not home_team or not away_team:
            continue

        home_entity = _load_team_entity(db, m.home_team_id)
        away_entity = _load_team_entity(db, m.away_team_id)
        pred = engine.predict_full(home_entity, away_entity, home_advantage=True)

        home_win_sim = sim_results_map.get(home_team.name, 0)
        away_win_sim = sim_results_map.get(away_team.name, 0)

        # Importance score: uncertainty + impact on contenders
        uncertainty = 1 - abs(pred.home_win_prob - 0.5) * 2
        contender_impact = max(home_win_sim, away_win_sim) / 100
        importance = uncertainty * 0.4 + contender_impact * 0.6

        scored.append({
            "match_id": str(m.id),
            "home_team": home_team.name,
            "away_team": away_team.name,
            "match_date": m.match_date.isoformat() if m.match_date else None,
            "stage": m.stage,
            "group_name": m.group_name,
            "home_win_prob": pred.home_win_prob,
            "draw_prob": pred.draw_prob,
            "away_win_prob": pred.away_win_prob,
            "most_likely_score": pred.most_likely_score,
            "confidence_index": pred.confidence_index,
            "surprise_risk": pred.surprise_risk,
            "importance": round(importance, 3),
            "contender_involved": home_win_sim > 1 or away_win_sim > 1,
        })

    scored.sort(key=lambda x: x["importance"], reverse=True)
    return {"matches": scored[:5], "top_match": scored[0] if scored else None}


@router.get("/team/{team_name}")
@cached("insights:team", ttl=120)
def get_team_insight(team_name: str, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.name == team_name).first()
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_name} not found")

    team_data = _load_team_data(db, team.id)

    latest_sim = (
        db.query(Simulation)
        .filter(Simulation.status == "completed")
        .order_by(Simulation.completed_at.desc())
        .first()
    )
    probs = None
    if latest_sim:
        result = (
            db.query(SimulationResult)
            .filter(
                SimulationResult.simulation_id == latest_sim.id,
                SimulationResult.team_id == team.id,
            )
            .first()
        )
        if result:
            n = max(latest_sim.num_simulations, 1)
            probs = {
                "win_prob": round(result.won_tournament / n * 100, 1),
                "final_prob": round(result.reached_final / n * 100, 1),
                "sf_prob": round(result.reached_semi_final / n * 100, 1),
                "qf_prob": round(result.reached_quarter_final / n * 100, 1),
                "r16_prob": round(result.reached_round_of_16 / n * 100, 1),
                "r32_prob": round(result.reached_round_of_32 / n * 100, 1),
                "avg_points": round(float(result.points), 2),
            }

    team_story = generate_team_story({
        **team_data,
        "win_prob": probs["win_prob"] if probs else 0,
    })

    # Most likely path analysis
    path = []
    if probs:
        stages = [
            ("Round of 32", probs.get("r32_prob", 100)),
            ("Round of 16", probs.get("r16_prob", 0)),
            ("Quarter-Final", probs.get("qf_prob", 0)),
            ("Semi-Final", probs.get("sf_prob", 0)),
            ("Final", probs.get("final_prob", 0)),
            ("Champion", probs.get("win_prob", 0)),
        ]
        for stage_name, stage_prob in stages:
            path.append({"stage": stage_name, "probability": stage_prob})

    # Hardest opponent: find upcoming match with highest opponent elo
    hardest = None
    upcoming = (
        db.query(Match)
        .filter(
            Match.status == "scheduled",
            (Match.home_team_id == team.id) | (Match.away_team_id == team.id),
        )
        .order_by(Match.match_date.asc())
        .first()
    )
    if upcoming:
        opp_id = upcoming.away_team_id if upcoming.home_team_id == team.id else upcoming.home_team_id
        opp = db.query(Team).filter(Team.id == opp_id).first()
        if opp:
            opp_elo = (
                db.query(EloRating)
                .filter(EloRating.team_id == opp.id)
                .order_by(EloRating.rating_date.desc())
                .first()
            )
            hardest = {
                "opponent_name": opp.name,
                "opponent_elo": opp_elo.elo_score if opp_elo else 1500,
                "match_date": upcoming.match_date.isoformat() if upcoming.match_date else None,
                "stage": upcoming.stage,
                "group_name": upcoming.group_name,
            }

    return {
        "team": team_data,
        "probabilities": probs,
        "story": team_story,
        "most_likely_path": path,
        "hardest_opponent": hardest,
    }


@router.get("/feed")
@cached("insights:feed", ttl=60)
def get_news_feed(db: Session = Depends(get_db)):
    teams = _get_simulation_probs(db)
    prev_teams = _get_prev_simulation_probs(db)
    insights = compute_insights(teams)
    for t in teams:
        team_entity = db.query(Team).filter(Team.name == t["team_name"]).first()
        if team_entity:
            latest_elo = (
                db.query(EloRating)
                .filter(EloRating.team_id == team_entity.id)
                .order_by(EloRating.rating_date.desc())
                .first()
            )
            t["elo_score"] = latest_elo.elo_score if latest_elo else 1500
    feed = generate_feed_events(teams, prev_teams, insights)
    return {"feed": feed[:20]}


@router.get("/qualification")
@cached("insights:qualification", ttl=120)
def get_qualification_heatmap(db: Session = Depends(get_db)):
    teams = _get_simulation_probs(db)
    heatmap = []
    for t in teams:
        heatmap.append({
            "team_name": t["team_name"],
            "r16": t.get("r16_prob", t.get("qf_prob", 0) + 5),
            "qf": t["qf_prob"],
            "sf": t["sf_prob"],
            "final": t["final_prob"],
            "champion": t["win_prob"],
        })
    return {"heatmap": heatmap}
