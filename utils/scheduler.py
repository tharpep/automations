import schedule
import time
import importlib.util
import sys
from pathlib import Path
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
    """Start the scheduler based on config.yaml schedules."""
    config = load_config(config_path)
    logger = setup_logger(__name__, config)

    schedules_config = config.get("schedules", [])

    if not schedules_config:
        logger.info("No schedules configured. Add schedules to config.yaml")
        return

    scheduled_count = 0
    for sched in schedules_config:
        script = sched.get("script")
        schedule_type = sched.get("schedule", "daily")
        schedule_time = sched.get("time", "09:00")
        enabled = sched.get("enabled", True)

        if not enabled:
            logger.info(f"Skipping disabled schedule: {script}")
            continue

        if schedule_type == "daily":
            schedule.every().day.at(schedule_time).do(run_script, script_path=script)
            logger.info(f"Scheduled {script} daily at {schedule_time}")
        elif schedule_type == "hourly":
            schedule.every().hour.do(run_script, script_path=script)
            logger.info(f"Scheduled {script} hourly")
        elif "minute" in schedule_type.lower():
            try:
                minutes = int(schedule_type.split()[1])
                schedule.every(minutes).minutes.do(run_script, script_path=script)
                logger.info(f"Scheduled {script} every {minutes} minutes")
            except (IndexError, ValueError):
                logger.error(f"Invalid schedule format: {schedule_type}")
                continue

        scheduled_count += 1

    if scheduled_count == 0:
        logger.info("No enabled schedules found")
        return

    logger.info(f"Scheduler started with {scheduled_count} schedule(s). Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped")
