"""
Base collector adapter — all data providers extend this.
Implements retry, rate-limit, cache, and logging.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable

import aiohttp
import httpx
from tenacity import before_sleep_log, retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def rate_limiter(calls_per_second: int):
    interval = 1.0 / calls_per_second
    last_called = [0.0]

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < interval:
                time.sleep(interval - elapsed)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result

        return wrapper

    return decorator


class BaseCollector(ABC):
    """Base class for all data collectors. Implements retry, rate-limit, and caching."""

    def __init__(self, base_url: str, api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._cache: dict[str, tuple[float, Any]] = {}
        self._cache_ttl = settings.cache_ttl

    @abstractmethod
    async def collect(self) -> list[dict[str, Any]]:
        """Collect data from the provider. Returns list of normalized records."""
        ...

    def _get_cached(self, key: str) -> Any | None:
        if key in self._cache:
            timestamp, data = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return data
            del self._cache[key]
        return None

    def _set_cache(self, key: str, data: Any) -> None:
        self._cache[key] = (time.time(), data)

    async def _fetch(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Fetch with retry logic via httpx."""
        for attempt in range(settings.collectors_retry_max_attempts):
            try:
                headers = {}
                if self.api_key:
                    headers["X-Auth-Token"] = self.api_key
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(url, params=params, headers=headers)
                    resp.raise_for_status()
                    return resp.json()
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                logger.warning(f"Fetch attempt {attempt + 1} failed for {url}: {e}")
                if attempt == settings.collectors_retry_max_attempts - 1:
                    raise
                await asyncio.sleep(settings.collectors_retry_backoff ** attempt)
        return {}
