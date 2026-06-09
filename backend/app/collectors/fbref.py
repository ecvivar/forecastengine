import logging

from app.collectors.base import BaseCollector
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class FBrefCollector(BaseCollector):
    """Collects advanced stats (xG, xGA, etc.) from FBref."""

    def __init__(self):
        super().__init__(base_url=settings.collectors_fbref_base_url)

    async def collect(self) -> list[dict]:
        logger.info("Collecting FBref stats...")
        data = await self._fetch(f"{self.base_url}/en/comps/1/stats/World-Cup-Stats")
        metrics = []
        for entry in data.get("players", []):
            metrics.append(
                {
                    "source": "fbref",
                    "team_name": entry.get("team"),
                    "player_name": entry.get("player"),
                    "xg": entry.get("xg"),
                    "xga": entry.get("xga"),
                    "non_penalty_xg": entry.get("npxg"),
                    "shots_on_target": entry.get("shots_on_target"),
                    "metric_date": entry.get("date"),
                }
            )
        return metrics
