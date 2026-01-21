"""
Automation runner - execute automations on-demand or start scheduler.

Usage:
    python runner.py <script_path>  # Run once
    python runner.py --scheduler    # Start scheduler
"""

import sys
import argparse
from pathlib import Path

from utils.scheduler import run_script, start_scheduler
from utils.logger import setup_logger
from utils.config_loader import load_config


def main():
    parser = argparse.ArgumentParser(description="Run automation scripts")
    parser.add_argument(
        "script",
        nargs="?",
        help="Path to script (e.g., scheduled/daily_summary.py)",
    )
    parser.add_argument(
        "--scheduler",
        action="store_true",
        help="Start the scheduler to run scripts on schedule",
    )

    args = parser.parse_args()

    config = load_config()
    logger = setup_logger(__name__, config)

    if args.scheduler:
        start_scheduler()
    elif args.script:
        script_path = Path(args.script)
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            sys.exit(1)
        logger.info(f"Running script: {script_path}")
        run_script(str(script_path))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
