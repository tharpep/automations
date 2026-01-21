import schedule
import time
import importlib.util
import sys
from pathlib import Path
from typing import Callable
from utils.logger import setup_logger
from utils.config_loader import load_config


def run_script(script_path: str):
    """Import and run a script module."""
    script_file = Path(script_path)
    if not script_file.exists():
        logger = setup_logger(__name__)
        logger.error(f"Script not found: {script_path}")
        return

    spec = importlib.util.spec_from_file_location("script_module", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["script_module"] = module
    spec.loader.exec_module(module)

    if hasattr(module, "main"):
        module.main()
    else:
        logger = setup_logger(__name__)
        logger.warning(f"Script {script_path} has no main() function")


def start_scheduler(config_path: str = "config/config.yaml"):
    """
    Start the scheduler based on config.yaml schedules.

    Config format:
    schedules:
      - script: scripts/category/script.py
        schedule: "daily"  # or "hourly", "every 5 minutes", cron-like
        time: "09:00"  # for daily schedules
    """
    config = load_config(config_path)
    logger = setup_logger(__name__, config)

    schedules = config.get("schedules", [])

    if not schedules:
        logger.info("No schedules configured. Run scripts manually or add schedules to config.yaml")
        return

    for schedule_config in schedules:
        script = schedule_config.get("script")
        schedule_type = schedule_config.get("schedule", "daily")
        schedule_time = schedule_config.get("time", "09:00")

        if schedule_type == "daily":
            schedule.every().day.at(schedule_time).do(run_script, script_path=script)
            logger.info(f"Scheduled {script} to run daily at {schedule_time}")
        elif schedule_type == "hourly":
            schedule.every().hour.do(run_script, script_path=script)
            logger.info(f"Scheduled {script} to run hourly")
        elif "minute" in schedule_type.lower():
            # Parse "every 5 minutes" or "every 30 minutes"
            try:
                minutes = int(schedule_type.split()[1])
                schedule.every(minutes).minutes.do(run_script, script_path=script)
                logger.info(f"Scheduled {script} to run every {minutes} minutes")
            except (IndexError, ValueError):
                logger.error(f"Invalid schedule format: {schedule_type}")

    logger.info("Scheduler started. Press Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped")
