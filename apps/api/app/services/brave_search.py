from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class BraveSearchService:
    endpoint = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self) -> None:
        self.enabled = bool(settings.brave_api_key)

    def search(self, query: str, count: int | None = None) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        try:
            with httpx.Client(timeout=settings.request_timeout_seconds) as client:
                response = client.get(
                    self.endpoint,
                    params={"q": query, "count": count or settings.max_results_per_query},
                    headers={"Accept": "application/json", "X-Subscription-Token": settings.brave_api_key or ""},
                )
                response.raise_for_status()
            data = response.json()
            return data.get("web", {}).get("results", [])
        except Exception:
            logger.exception("Brave search failed for query=%s", query)
            return []

