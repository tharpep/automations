"""
---
name: daily-context
type: scheduled
schedule: "0 9 * * *"
timezone: America/New_York
enabled: true
---
"""

from utils import GatewayClient, setup_logger, load_config


def main():
    config = load_config()
    logger = setup_logger(__name__, config)

    logger.info("Starting daily context")

    with GatewayClient() as client:
        health = client.health()
        logger.info(f"Gateway: {health.get('status')}")

        calendar = client.get_calendar_today()
        events = calendar.get("events", [])

        if not events:
            message = "Good morning! You have a clear schedule today. ☀️"
            client.notify(title="Good Morning", message=message)
            logger.info("No events - sent default message")
            return

        event_list = "\n".join([f"- {e['title']} at {e['start']}" for e in events])
        prompt = (
            f"Here's my calendar for today:\n{event_list}\n\n"
            f"Give me a casual, friendly 1-2 sentence summary of my day. "
            f"Keep it brief and conversational."
        )

        try:
            response = client.ai_chat([{"role": "user", "content": prompt}])
            summary = response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"AI failed, falling back: {e}")
            summary = f"Good morning! You have {len(events)} event(s) today. 📅"

        client.notify(title="Good Morning", message=summary)
        logger.info("Notification sent")


if __name__ == "__main__":
    main()
