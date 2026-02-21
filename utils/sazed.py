"""Sazed agent client for automations."""

import os

import httpx


class SazedClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = base_url or os.getenv("SAZED_URL", "http://localhost:8000")
        self.api_key = api_key or os.getenv("SAZED_API_KEY", "")

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        self._client = httpx.Client(base_url=self.base_url, timeout=60.0, headers=headers)

    def chat(self, message: str, session_id: str | None = None) -> str:
        """Send a message to the Sazed agent and return the response text."""
        payload: dict = {"message": message}
        if session_id:
            payload["session_id"] = session_id

        response = self._client.post("/chat", json=payload)
        response.raise_for_status()
        return response.json()["response"]

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
