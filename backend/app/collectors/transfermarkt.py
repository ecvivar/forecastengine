import logging

from app.collectors.base import BaseCollector
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TransfermarktCollector(BaseCollector):
    """Collects squad market values and player data from Transfermarkt."""

    def __init__(self):
        super().__init__(base_url=settings.collectors_transfermarkt_base_url)

    async def collect(self) -> list[dict]:
        logger.info("Collecting Transfermarkt data...")
        data = await self._fetch(f"{self.base_url}/api/playerdata")
        players = []
        for entry in data.get("players", []):
            players.append(
                {
                    "source": "transfermarkt",
                    "team_name": entry.get("team"),
                    "player_name": entry.get("name"),
                    "position": entry.get("position"),
                    "market_value": entry.get("marketValue"),
                    "age": entry.get("age"),
                    "nationality": entry.get("nationality"),
                }
            )
        return players
