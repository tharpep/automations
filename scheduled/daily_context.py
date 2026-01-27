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
        
        try:
            context = client.context_now()
        except Exception as e:
            logger.warning(f"Context unavailable: {e}")
            context = {}
        
        parts = ["Good morning!"]
        if context.get("calendar"):
            parts.append(f"📅 {len(context['calendar'].get('events', []))} events")
        if context.get("tasks"):
            parts.append(f"✅ {len(context['tasks'].get('items', []))} tasks")
        
        client.notify(title="Daily Context", message="\n".join(parts))
        logger.info("Notification sent")


if __name__ == "__main__":
    main()
