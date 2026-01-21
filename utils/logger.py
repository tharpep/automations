import logging
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str, config: Optional[dict] = None, log_file: Optional[str] = None
) -> logging.Logger:

    logger = logging.getLogger(name)

    if config and "logging" in config:
        log_config = config["logging"]
        level = getattr(logging, log_config.get("level", "INFO"))
        fmt = log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    else:
        level = logging.INFO
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logger.setLevel(level)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(fmt)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    if log_file:
        file_path = Path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(fmt)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
