"""
Example automation script.

This script demonstrates the standard structure for automation scripts.
"""

import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.config_loader import load_config
from utils.logger import setup_logger


def main():
    """Main execution function."""
    # Load configuration
    config = load_config()

    # Set up logger
    logger = setup_logger(__name__, config)

    logger.info("Example script started")
    # Your script logic here
    logger.info("Example script completed")


if __name__ == "__main__":
    main()
