"""
---
name: weekly-context
type: scheduled
schedule: "0 18 * * 0"
timezone: America/New_York
enabled: true
---
"""

import uuid

from utils import SazedClient, GatewayClient, setup_logger, load_config

# Stable UUID for the weekly automation session — deterministic, persists memory across runs
SESSION_ID = str(uuid.uuid5(uuid.NAMESPACE_DNS, "automation-weekly"))

PROMPT = (
    "Check my calendar and tasks for the next 7 days. "
    "Give me a weekly preview in exactly 1-2 sentences, 35 words max. "
    "Lead with the busiest day or most important deadline. "
    "No greeting, no sign-off, no filler, no markdown — plain text only."
)


def main():
    config = load_config()
    logger = setup_logger(__name__, config)

    logger.info("Starting weekly context")

    try:
        with SazedClient() as agent:
            summary = agent.chat(PROMPT, session_id=SESSION_ID)

        logger.info(f"Agent response: {summary}")
    except Exception as e:
        logger.warning(f"Agent call failed, falling back to gateway: {e}")
        summary = _fallback_summary(logger)

    with GatewayClient() as gateway:
        gateway.notify(title="Weekly Preview", message=summary)

    logger.info("Notification sent")


def _fallback_summary(logger) -> str:
    """Minimal fallback if the agent is unavailable."""
    try:
        with GatewayClient() as client:
            events = client.get_calendar_events(days=7).get("events", [])
            tasks = client.get_tasks_upcoming(days=7).get("tasks", [])
        parts = []
        if events:
            parts.append(f"{len(events)} event(s) this week")
        if tasks:
            parts.append(f"{len(tasks)} task(s) upcoming")
        return ", ".join(parts) + "." if parts else "Clear week ahead."
    except Exception as e:
        logger.error(f"Fallback also failed: {e}")
        return "Could not retrieve weekly context."


if __name__ == "__main__":
    main()
