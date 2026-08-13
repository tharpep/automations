import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, Literal

import httpx

from utils.logger import setup_logger
from utils.config_loader import load_config
from app import runs

logger = setup_logger(__name__)
BASE_PATH = Path(__file__).parent.parent

API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "")
API_GATEWAY_KEY = os.getenv("API_GATEWAY_KEY", "")


def _run_script(script_path: str) -> None:
    full_path = BASE_PATH / script_path
    if not full_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    spec = importlib.util.spec_from_file_location("script_module", full_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["script_module"] = module
    spec.loader.exec_module(module)

    if not hasattr(module, "main"):
        raise AttributeError(f"Script {script_path} has no main() function")

    module.main()


def _run_api_call(api_call: dict[str, Any], automation_name: str) -> None:
    method = api_call.get("method", "GET")
    path = api_call["path"]
    payload = api_call.get("payload")

    headers = {"X-API-Key": API_GATEWAY_KEY} if API_GATEWAY_KEY else {}
    url = f"{API_GATEWAY_URL.rstrip('/')}/{path.lstrip('/')}"

    with httpx.Client(timeout=30.0) as client:
        response = client.request(method, url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.text[:500]

    if api_call.get("notify"):
        template = api_call.get("notify_template", "{name} finished: {result}")
        message = template.format(name=automation_name, result=result)
        try:
            with httpx.Client(timeout=10.0) as client:
                client.post(
                    f"{API_GATEWAY_URL.rstrip('/')}/notify",
                    json={"title": automation_name, "message": message[:1024]},
                    headers=headers,
                )
        except httpx.HTTPError as e:
            logger.warning(f"Notify failed for {automation_name}: {e}")


def run_automation(entry: dict[str, Any], triggered_by: Literal["schedule", "manual"] = "schedule") -> None:
    automation_id = entry["id"]
    run_id = runs.start_run(automation_id, triggered_by)
    logger.info(f"Starting automation {automation_id} (triggered_by={triggered_by})")

    try:
        if entry["type"] == "script":
            _run_script(entry["script"])
        elif entry["type"] == "api_call":
            _run_api_call(entry["api_call"], entry.get("name", automation_id))
        else:
            raise ValueError(f"Unknown automation type: {entry['type']}")

        runs.finish_run(run_id, "success")
        logger.info(f"Automation {automation_id} finished successfully")
    except Exception as e:
        runs.finish_run(run_id, "error", error=str(e))
        logger.error(f"Automation {automation_id} failed: {e}")
