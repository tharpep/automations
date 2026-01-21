import yaml
from pathlib import Path
from dotenv import load_dotenv


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Load configuration from YAML and .env files."""
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)

    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_file, "r") as f:
        config = yaml.safe_load(f) or {}


    return config
