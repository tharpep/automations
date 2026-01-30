"""
---
name: daily-context
type: scheduled
schedule: "0 9 * * *"
timezone: America/New_York
enabled: true
---
"""

from datetime import datetime

from utils import GatewayClient, setup_logger, load_config


def main():
    config = load_config()
    logger = setup_logger(__name__, config)

    logger.info("Starting daily context")

    with GatewayClient() as client:
        health = client.health()
        logger.info(f"Gateway: {health.get('status')}")

        calendar = client.get_calendar_events(days=1)
        events = calendar.get("events", [])

        emails = client.get_email_recent(hours=24)
        messages = emails.get("messages", [])

        tasks = client.get_tasks_upcoming(days=1)
        upcoming_tasks = tasks.get("tasks", [])

        # Get current date for context
        today = datetime.now().strftime("%A, %B %d, %Y")

        if not events and not messages and not upcoming_tasks:
            message = "You have a clear schedule, no urgent emails, and no tasks due today. Enjoy your day! ☀️"
            client.notify(title="Good Morning", message=message)
            logger.info("No events, emails, or tasks - sent default message")
            return

        context_parts = []

        if events:
            event_list = "\n".join([f"- {e['title']} at {e['start']}" for e in events])
            context_parts.append(f"CALENDAR:\n{event_list}")

        if messages:
            recent_messages = messages[:10]
            email_list = "\n".join([f"- {m['subject']} (from {m['sender']})" for m in recent_messages])
            context_parts.append(f"EMAILS (last 24h, {len(messages)} total):\n{email_list}")

        if upcoming_tasks:
            task_list = "\n".join([
                f"- {t['title']} [{t['list_name']}]"
                for t in upcoming_tasks[:10]
            ])
            context_parts.append(f"TASKS (due today, {len(upcoming_tasks)} total):\n{task_list}")

        full_context = "\n\n".join(context_parts)

        prompt = (
            f"Today is {today}. Here's my context:\n\n{full_context}\n\n"
            f"Give me a concise, casual, friendly 3-4 sentence morning briefing. "
            f"Skip greetings and don't mention today's date (I already know it's {today}). "
            f"Lead with the most important or time-sensitive thing. "
            f"Ignore promotional emails and marketing content. "
        )

        try:
            response = client.ai_chat([{"role": "user", "content": prompt}])
            summary = response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"AI failed, falling back: {e}")
            summary = (
                f"You have {len(events)} event(s), "
                f"{len(messages)} email(s), and {len(upcoming_tasks)} task(s) due today. 📅"
            )

        client.notify(title="Good Morning", message=summary)
        logger.info("Notification sent")


if __name__ == "__main__":
    main()
