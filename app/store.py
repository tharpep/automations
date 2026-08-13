"""Reads and writes config/config.yaml's `schedules` list - the ONLY thing this API
ever mutates. Script frontmatter (the GCP Cloud Scheduler source of truth) is never
touched. Every write is committed and pushed to the automations GitHub repo so it
survives redeploys and stays versioned, matching how the rest of this setup works.
"""

import subprocess
from pathlib import Path
from typing import Any

import yaml

BASE_PATH = Path(__file__).parent.parent
CONFIG_PATH = BASE_PATH / "config" / "config.yaml"


def _read_raw() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f) or {}


def get_schedules() -> list[dict[str, Any]]:
    return _read_raw().get("schedules", [])


def get_entry(automation_id: str) -> dict[str, Any] | None:
    for entry in get_schedules():
        if entry.get("id") == automation_id:
            return entry
    return None


def _write_raw(config: dict[str, Any]) -> None:
    with open(CONFIG_PATH, "w") as f:
        yaml.safe_dump(config, f, sort_keys=False, default_flow_style=False)


def _commit_and_push(message: str) -> None:
    try:
        subprocess.run(["git", "add", "config/config.yaml"], cwd=BASE_PATH, check=True)
        result = subprocess.run(
            ["git", "commit", "-m", message], cwd=BASE_PATH, capture_output=True, text=True
        )
        # Nothing to commit is not an error (e.g. a no-op update).
        if result.returncode != 0 and "nothing to commit" not in result.stdout:
            raise RuntimeError(f"git commit failed: {result.stdout}\n{result.stderr}")
        subprocess.run(["git", "push", "origin", "main"], cwd=BASE_PATH, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"git operation failed: {e}") from e


def upsert_entry(entry: dict[str, Any], commit_message: str) -> None:
    config = _read_raw()
    schedules = config.setdefault("schedules", [])

    for i, existing in enumerate(schedules):
        if existing.get("id") == entry["id"]:
            schedules[i] = entry
            break
    else:
        schedules.append(entry)

    _write_raw(config)
    _commit_and_push(commit_message)


def delete_entry(automation_id: str, commit_message: str) -> bool:
    config = _read_raw()
    schedules = config.get("schedules", [])
    new_schedules = [e for e in schedules if e.get("id") != automation_id]

    if len(new_schedules) == len(schedules):
        return False

    config["schedules"] = new_schedules
    _write_raw(config)
    _commit_and_push(commit_message)
    return True
