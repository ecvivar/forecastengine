import logging

from app.collectors.base import BaseCollector
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class FifaRankingCollector(BaseCollector):
    """Collects FIFA World Rankings from the official FIFA API."""

    def __init__(self):
        super().__init__(base_url=settings.collectors_fifa_base_url)

    async def collect(self) -> list[dict]:
        logger.info("Collecting FIFA rankings...")
        data = await self._fetch(f"{self.base_url}/ranking")
        rankings = []
        for entry in data.get("results", []):
            rankings.append(
                {
                    "source": "fifa",
                    "rank": entry.get("rank"),
                    "team_name": entry.get("name"),
                    "fifa_code": entry.get("code"),
                    "confederation": entry.get("confederation"),
                    "total_points": entry.get("points"),
                    "previous_rank": entry.get("previousRank"),
                    "ranking_date": entry.get("date"),
                }
            )
        return rankings
