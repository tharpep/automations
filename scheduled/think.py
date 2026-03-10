"""
---
name: think
type: scheduled
schedule: "50 8,13,20 * * *"
timezone: America/New_York
enabled: true
---
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from utils import SazedClient, setup_logger, load_config


def main():
    config = load_config()
    logger = setup_logger(__name__, config)

    hour = datetime.now(ZoneInfo("America/New_York")).hour
    context = "morning" if hour < 12 else "evening" if hour >= 18 else "midday"

    logger.info(f"Starting think — context={context}")

    try:
        with SazedClient() as agent:
            result = agent.think(context=context, timezone="America/New_York")

        acted = result.get("acted", False)
        summary = result.get("summary", "")
        logger.info(f"Think complete — acted={acted}, summary='{summary[:200]}'")
    except Exception as e:
        logger.warning(f"Think failed: {e}")


if __name__ == "__main__":
    main()
