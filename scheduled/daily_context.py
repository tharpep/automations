"""
---
name: daily-context
type: scheduled
schedule: "0 9 * * *"
timezone: America/New_York
enabled: false
---
"""

import uuid

from utils import SazedClient, GatewayClient, setup_logger, load_config

# Stable UUID for the daily automation session — deterministic, persists memory across runs
SESSION_ID = str(uuid.uuid5(uuid.NAMESPACE_DNS, "automation-daily"))

PROMPT = (
    "Check my calendar, tasks due today, and unread emails. "
    "Give me a morning briefing in exactly 1-2 sentences, 35 words max. "
    "Lead with the single most urgent or time-sensitive thing. "
    "No greeting, no sign-off, no filler, no markdown — plain text only."
)


def main():
    config = load_config()
    logger = setup_logger(__name__, config)

    logger.info("Starting daily context")

    try:
        with SazedClient() as agent:
            summary = agent.chat(PROMPT, session_id=SESSION_ID)

        logger.info(f"Agent response: {summary}")
    except Exception as e:
        logger.warning(f"Agent call failed, falling back to gateway: {e}")
        summary = _fallback_summary(logger)

    with GatewayClient() as gateway:
        gateway.notify(title="Good Morning", message=summary)

    logger.info("Notification sent")


def _fallback_summary(logger) -> str:
    """Minimal fallback if the agent is unavailable."""
    try:
        with GatewayClient() as client:
            events = client.get_calendar_events(days=1).get("events", [])
            tasks = client.get_tasks_upcoming(days=1).get("tasks", [])
        parts = []
        if events:
            parts.append(f"{len(events)} event(s) today")
        if tasks:
            parts.append(f"{len(tasks)} task(s) due")
        return ", ".join(parts) + "." if parts else "Clear schedule today."
    except Exception as e:
        logger.error(f"Fallback also failed: {e}")
        return "Could not retrieve daily context."


if __name__ == "__main__":
    main()
