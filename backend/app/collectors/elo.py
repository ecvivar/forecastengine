import logging

from app.collectors.base import BaseCollector
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EloRatingCollector(BaseCollector):
    """Collects Elo ratings from eloratings.net."""

    def __init__(self):
        super().__init__(base_url=settings.collectors_elo_base_url)

    async def collect(self) -> list[dict]:
        logger.info("Collecting Elo ratings...")
        data = await self._fetch(f"{self.base_url}/world.json")
        ratings = []
        for entry in data:
            ratings.append(
                {
                    "source": "elo",
                    "team_name": entry.get("name"),
                    "fifa_code": entry.get("code"),
                    "elo_score": entry.get("elo"),
                    "rank": entry.get("rank"),
                    "rating_date": entry.get("date"),
                }
            )
        return ratings
