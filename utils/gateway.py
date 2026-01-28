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
        """Get gateway health status."""
        response = self._client.get("/health")
        response.raise_for_status()
        return response.json()

    def integrations(self) -> dict:
        """Get integration status."""
        response = self._client.get("/health/integrations")
        response.raise_for_status()
        return response.json()

    def context_now(self) -> dict:
        """Get aggregated context snapshot."""
        response = self._client.get("/context/now")
        response.raise_for_status()
        return response.json()

    def ai_chat(self, messages: list[dict], model: str | None = None, stream: bool = False) -> dict:
        """Send a chat completion request."""
        payload = {"messages": messages, "stream": stream}
        if model:
            payload["model"] = model
        response = self._client.post("/ai/v1/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
