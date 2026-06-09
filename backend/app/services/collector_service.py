import logging
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.collectors.elo import EloRatingCollector
from app.collectors.fbref import FBrefCollector
from app.collectors.fifa import FifaRankingCollector
from app.collectors.football_data import FootballDataCollector
from app.collectors.transfermarkt import TransfermarktCollector
from app.models.elo_rating import EloRating
from app.models.fifa_ranking import FifaRanking
from app.models.player import Player
from app.models.team import Team
from app.models.xg_metrics import XGMetrics

logger = logging.getLogger(__name__)


class CollectorService:
    """Orchestrates all data collectors and persists to database."""

    def __init__(self, db: Session):
        self.db = db
        self.collectors = {
            "fifa": FifaRankingCollector(),
            "elo": EloRatingCollector(),
            "fbref": FBrefCollector(),
            "transfermarkt": TransfermarktCollector(),
            "football_data": FootballDataCollector(),
        }

    async def collect_all(self) -> dict[str, int]:
        results = {}
        for name, collector in self.collectors.items():
            try:
                data = await collector.collect()
                count = self._persist(name, data)
                results[name] = count
                logger.info(f"{name}: collected and persisted {count} records")
            except Exception as e:
                logger.error(f"{name}: collection failed - {e}")
                results[name] = 0
        return results

    async def collect_source(self, source: str) -> int:
        collector = self.collectors.get(source)
        if not collector:
            raise ValueError(f"Unknown collector: {source}")
        data = await collector.collect()
        return self._persist(source, data)

    def _persist(self, source: str, data: list[dict]) -> int:
        today = date.today()
        count = 0

        for record in data:
            try:
                team_name = record.get("team_name", "")
                team = self.db.query(Team).filter(
                    (Team.name == team_name) | (Team.fifa_code == record.get("fifa_code", ""))
                ).first()

                if not team and source in ("football_data", "fifa"):
                    team = Team(
                        name=team_name,
                        fifa_code=record.get("fifa_code"),
                        continent=record.get("confederation"),
                    )
                    self.db.add(team)
                    self.db.flush()

                if not team:
                    logger.warning(f"Skipping {source} record: team '{team_name}' not found")
                    continue

                if source == "fifa":
                    self._persist_fifa(record, team.id, today)
                elif source == "elo":
                    self._persist_elo(record, team.id, today)
                elif source == "fbref":
                    self._persist_fbref(record, team.id, today)
                elif source == "transfermarkt":
                    self._persist_transfermarkt(record, team.id)
                elif source == "football_data":
                    self._persist_football_data(record, team)

                count += 1
            except Exception as e:
                logger.error(f"Error persisting {source} record: {e}")

        self.db.commit()
        return count

    def _persist_fifa(self, record: dict, team_id, today: date):
        ranking = FifaRanking(
            team_id=team_id,
            ranking_date=today,
            rank=record.get("rank", 100),
            previous_rank=record.get("previous_rank"),
            total_points=record.get("total_points", 0),
            confederation=record.get("confederation"),
        )
        self.db.add(ranking)

    def _persist_elo(self, record: dict, team_id, today: date):
        elo = EloRating(
            team_id=team_id,
            rating_date=today,
            elo_score=record.get("elo_score", 1500),
            rank=record.get("rank"),
        )
        self.db.add(elo)

    def _persist_fbref(self, record: dict, team_id, today: date):
        xg = XGMetrics(
            team_id=team_id,
            metric_date=today,
            xg_for=record.get("xg", 0.0),
            xg_against=record.get("xga", 0.0),
            non_penalty_xg=record.get("non_penalty_xg"),
            shots_on_target=record.get("shots_on_target"),
            matches_sampled=1,
        )
        self.db.add(xg)

    def _persist_transfermarkt(self, record: dict, team_id):
        player = Player(
            team_id=team_id,
            name=record.get("player_name", "Unknown"),
            position=record.get("position"),
            market_value=record.get("market_value"),
        )
        self.db.add(player)

    def _persist_football_data(self, record: dict, team: Team):
        if record.get("founded_year"):
            team.founded_year = record.get("founded_year")
        if record.get("flag_url"):
            team.flag_url = record.get("flag_url")
