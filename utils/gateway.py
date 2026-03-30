"""API Gateway client for automations."""

import os
from typing import Any

import httpx


class GatewayClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = base_url or os.getenv("API_GATEWAY_URL", "https://api-gateway-252332699398.us-central1.run.app")
        self.api_key = api_key or os.getenv("API_GATEWAY_KEY", "")
        
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        self._client = httpx.Client(base_url=self.base_url, timeout=30.0, headers=headers)

    def notify(self, title: str, message: str, priority: int = 0) -> dict:
        """Send a push notification via the gateway."""
        response = self._client.post("/notify", json={
            "title": title,
            "message": message,
            "priority": priority,
        })
        response.raise_for_status()
        return response.json()

    def health(self) -> dict:
        response = self._client.get("/health")
        response.raise_for_status()
        return response.json()

    def integrations(self) -> dict:
        response = self._client.get("/health/integrations")
        response.raise_for_status()
        return response.json()

    def context_now(self) -> dict:
        """Get aggregated context snapshot."""
        response = self._client.get("/context/now")
        response.raise_for_status()
        return response.json()

    def ai_chat(self, messages: list[dict], model: str | None = None, stream: bool = False) -> dict:
        payload = {"messages": messages, "stream": stream}
        if model:
            payload["model"] = model
        response = self._client.post("/ai/v1/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()

    def get_calendar_events(self, days: int = 1) -> dict:
        """Get calendar events for the next N days.

        Args:
            days: Number of days to look ahead (default: 1 for today)
        """
        if days == 1:
            # Use optimized today endpoint
            response = self._client.get("/calendar/today")
        else:
            response = self._client.get(f"/calendar/events?days={days}")
        response.raise_for_status()
        return response.json()

    def get_email_recent(self, hours: int = 24) -> dict:
        """Get recent email messages from primary inbox.

        Args:
            hours: Number of hours to look back (default: 24)
        """
        response = self._client.get(f"/email/recent?hours={hours}")
        response.raise_for_status()
        return response.json()

    def get_tasks_upcoming(self, days: int = 7) -> dict:
        """Get upcoming tasks from configured lists.

        Args:
            days: Number of days to look ahead for due dates (default: 7)
        """
        response = self._client.get(f"/tasks/upcoming?days={days}")
        response.raise_for_status()
        return response.json()

    def aggregate_search(
        self,
        query: str,
        max_results: int = 25,
        platforms: list[str] | None = None,
        since: str | None = None,
    ) -> dict:
        """Search across all configured platforms and return aggregated results.

        Args:
            query: Search query string.
            max_results: Maximum total results across all platforms (default 25).
            platforms: Specific platforms to search. Options: 'reddit', 'hn', 'bluesky',
                       'gnews', 'google_news_rss', 'rss'. Omit for all available.
            since: ISO 8601 timestamp — only return results newer than this.
                   Useful for polling automations to avoid re-alerting on old results.
        """
        payload: dict = {"query": query, "max_results": max_results}
        if platforms:
            payload["platforms"] = platforms
        if since:
            payload["since"] = since
        response = self._client.post("/multi-search/aggregate", json=payload)
        response.raise_for_status()
        return response.json()

    def search_platform(
        self,
        platform: str,
        query: str,
        max_results: int = 10,
        since: str | None = None,
    ) -> dict:
        """Search a single platform directly.

        Args:
            platform: One of 'reddit', 'hn', 'bluesky', 'gnews', 'google-news-rss', 'rss'.
            query: Search query string.
            max_results: Maximum results to return (default 10).
            since: ISO 8601 timestamp — only return results newer than this.
        """
        payload: dict = {"query": query, "max_results": max_results}
        if since:
            payload["since"] = since
        response = self._client.post(f"/multi-search/{platform}", json=payload)
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
