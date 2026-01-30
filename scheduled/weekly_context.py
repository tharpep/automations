"""
---
name: weekly-context
type: scheduled
schedule: "0 18 * * 0"
timezone: America/New_York
enabled: true
---
"""

from utils import GatewayClient, setup_logger, load_config


def main():
    config = load_config()
    logger = setup_logger(__name__, config)

    logger.info("Starting weekly context")

    with GatewayClient() as client:
        health = client.health()
        logger.info(f"Gateway: {health.get('status')}")

        calendar = client.get_calendar_events(days=7)
        events = calendar.get("events", [])

        tasks = client.get_tasks_upcoming(days=7)
        upcoming_tasks = tasks.get("tasks", [])

        if not events and not upcoming_tasks:
            message = "Your week looks wide open! No scheduled events or pressing tasks. Time to make some plans or just enjoy the freedom. 🌴"
            client.notify(title="Weekly Preview", message=message)
            logger.info("No events or tasks - sent default message")
            return

        context_parts = []

        if events:
            event_list = "\n".join([f"- {e['title']} ({e['start'][:10]})" for e in events[:15]])
            context_parts.append(f"CALENDAR (next 7 days, {len(events)} total):\n{event_list}")

        if upcoming_tasks:
            task_list = "\n".join([
                f"- {t['title']}" + (f" (due {t['due'][:10]})" if t.get('due') else "") + f" [{t['list_name']}]"
                for t in upcoming_tasks[:15]
            ])
            context_parts.append(f"TASKS (next 7 days, {len(upcoming_tasks)} total):\n{task_list}")

        full_context = "\n\n".join(context_parts)

        prompt = (
            f"Here's my week ahead:\n\n{full_context}\n\n"
            f"Give me a short, concise, 3-4 sentence weekly preview. "
            f" Skip a greeting and instead lead with the most important or time-sensitive thing. "
            f"Highlight key commitments, busy days, or important deadlines. "
            f"Keep it motivating and help me feel prepared. "
        )

        try:
            response = client.ai_chat([{"role": "user", "content": prompt}])
            summary = response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"AI failed, falling back: {e}")
            summary = (
                f"Week ahead: {len(events)} event(s) and {len(upcoming_tasks)} task(s) "
                f"scheduled. Check your calendar for details. 📅"
            )

        client.notify(title="Weekly Preview", message=summary)
        logger.info("Notification sent")


if __name__ == "__main__":
    main()
