"""Sazed agent client for automations."""

import os
import re

import httpx


def strip_markdown(text: str) -> str:
    """Remove common markdown formatting for plain-text delivery (e.g. Pushover)."""
    # Bold / italic: ***text***, **text**, *text*, __text__, _text_
    text = re.sub(r'\*{1,3}(.+?)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,2}(.+?)_{1,2}', r'\1', text)
    # Inline code
    text = re.sub(r'`(.+?)`', r'\1', text)
    # Headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Bullet points — replace with a dash-free version
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    # Numbered lists
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    # Collapse excess whitespace/newlines
    text = re.sub(r'\n{2,}', ' ', text)
    return text.strip()


class SazedClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = base_url or os.getenv("SAZED_URL", "http://localhost:8000")
        self.api_key = api_key or os.getenv("SAZED_API_KEY", "")

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        self._client = httpx.Client(base_url=self.base_url, timeout=60.0, headers=headers)

    def chat(self, message: str, session_id: str | None = None) -> str:
        payload: dict = {"message": message}
        if session_id:
            payload["session_id"] = session_id

        response = self._client.post("/chat", json=payload)
        response.raise_for_status()
        return strip_markdown(response.json()["response"])

    def think(
        self,
        context: str | None = None,
        timezone: str | None = None,
        trigger: str | None = None,
        session_id: str | None = None,
    ) -> dict:
        """Trigger an autonomous think session. Returns {"session_id", "acted", "summary"}."""
        payload: dict = {}
        if context:
            payload["context"] = context
        if timezone:
            payload["timezone"] = timezone
        if trigger:
            payload["trigger"] = trigger
        if session_id:
            payload["session_id"] = session_id

        response = self._client.post("/think", json=payload, timeout=120.0)
        response.raise_for_status()
        return response.json()

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
