import uuid

import pandas as pd
from sqlalchemy.orm import Session, joinedload

from app.engine.igf import IGFEngine, IGFConfig
from app.models.elo_rating import EloRating
from app.models.fifa_ranking import FifaRanking
from app.models.team import Team
from app.models.xg_metrics import XGMetrics
from app.schemas.ranking import IGFScoreResponse


class RankingService:
    def __init__(self, db: Session):
        self.db = db
        self.igf_engine = IGFEngine()

    def get_latest_elo(self, limit: int = 20) -> list[dict]:
        results = (
            self.db.query(EloRating)
            .options(joinedload(EloRating.team))
            .order_by(EloRating.rating_date.desc(), EloRating.elo_score.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "team_id": r.team_id,
                "team_name": r.team.name,
                "elo_score": r.elo_score,
                "rank": r.rank,
                "rating_date": r.rating_date.isoformat(),
            }
            for r in results
        ]

    def get_latest_fifa(self, limit: int = 20) -> list[dict]:
        results = (
            self.db.query(FifaRanking)
            .options(joinedload(FifaRanking.team))
            .order_by(FifaRanking.ranking_date.desc(), FifaRanking.rank.asc())
            .limit(limit)
            .all()
        )
        return [
            {
                "team_id": r.team_id,
                "team_name": r.team.name,
                "rank": r.rank,
                "total_points": r.total_points,
                "confederation": r.confederation,
                "ranking_date": r.ranking_date.isoformat(),
            }
            for r in results
        ]

    def compute_igf(self) -> list[IGFScoreResponse]:
        teams = self.db.query(Team).all()
        rows = []
        for team in teams:
            latest_elo = (
                self.db.query(EloRating)
                .filter(EloRating.team_id == team.id)
                .order_by(EloRating.rating_date.desc())
                .first()
            )
            latest_fifa = (
                self.db.query(FifaRanking)
                .filter(FifaRanking.team_id == team.id)
                .order_by(FifaRanking.ranking_date.desc())
                .first()
            )
            latest_xg = (
                self.db.query(XGMetrics)
                .filter(XGMetrics.team_id == team.id)
                .order_by(XGMetrics.metric_date.desc())
                .first()
            )
            rows.append(
                {
                    "team_name": team.name,
                    "elo_score": latest_elo.elo_score if latest_elo else 1500,
                    "fifa_rank": latest_fifa.rank if latest_fifa else 100,
                    "xg_for": latest_xg.xg_for if latest_xg else 1.0,
                    "xg_against": latest_xg.xg_against if latest_xg else 1.0,
                }
            )

        df = pd.DataFrame(rows)
        scores = self.igf_engine.compute_team_scores(df)

        result = []
        for team in teams:
            if team.name in scores:
                s = scores[team.name]
                result.append(
                    IGFScoreResponse(
                        team_id=team.id,
                        team_name=team.name,
                        igf_score=s["igf_score"],
                        components=s["components"],
                    )
                )

        result.sort(key=lambda x: x.igf_score, reverse=True)
        return result
