import logging

from app.collectors.base import BaseCollector
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class FootballDataCollector(BaseCollector):
    """Collects match results, standings, and team data from football-data.org."""

    def __init__(self):
        super().__init__(
            base_url=settings.collectors_football_data_base_url,
            api_key=settings.collectors_football_data_api_key,
        )

    async def collect(self) -> list[dict]:
        logger.info("Collecting Football Data...")
        data = await self._fetch(f"{self.base_url}/teams")
        teams = []
        for entry in data.get("teams", []):
            teams.append(
                {
                    "source": "football_data",
                    "team_name": entry.get("name"),
                    "fifa_code": entry.get("tla"),
                    "flag_url": entry.get("crest"),
                    "founded_year": entry.get("founded"),
                    "venue": entry.get("venue"),
                }
            )
        return teams
