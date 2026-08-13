import json
import time
import uuid
from pathlib import Path
from typing import Any, Literal, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
RUNS_FILE = DATA_DIR / "runs.json"
RETENTION_DAYS = 30
MAX_RUNS = 500


def _read() -> list[dict[str, Any]]:
    try:
        return json.loads(RUNS_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _write(runs: list[dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - RETENTION_DAYS * 86400
    pruned = [r for r in runs if r["started_at"] >= cutoff][-MAX_RUNS:]
    RUNS_FILE.write_text(json.dumps(pruned))


def start_run(automation_id: str, triggered_by: Literal["schedule", "manual"]) -> str:
    run_id = str(uuid.uuid4())
    runs = _read()
    runs.append(
        {
            "id": run_id,
            "automation_id": automation_id,
            "started_at": time.time(),
            "finished_at": None,
            "status": "running",
            "error": None,
            "triggered_by": triggered_by,
        }
    )
    _write(runs)
    return run_id


def finish_run(run_id: str, status: Literal["success", "error"], error: Optional[str] = None) -> None:
    runs = _read()
    for r in runs:
        if r["id"] == run_id:
            r["finished_at"] = time.time()
            r["status"] = status
            r["error"] = error
            break
    _write(runs)


def get_runs(automation_id: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]:
    runs = _read()
    if automation_id:
        runs = [r for r in runs if r["automation_id"] == automation_id]
    return sorted(runs, key=lambda r: r["started_at"], reverse=True)[:limit]


def get_last_run(automation_id: str) -> Optional[dict[str, Any]]:
    matches = get_runs(automation_id, limit=1)
    return matches[0] if matches else None
