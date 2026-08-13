import threading
import time
from contextlib import asynccontextmanager

import schedule as schedule_lib
from fastapi import FastAPI, HTTPException

from app import discovery, executor, runs, store
from app.models import AutomationOut, CreateApiCallAutomation, UpdateAutomation
from utils.logger import setup_logger

logger = setup_logger(__name__)
RELOAD_INTERVAL_SECONDS = 30

_scheduler_stop = threading.Event()


def _register_jobs() -> None:
    schedule_lib.clear()
    for entry in store.get_schedules():
        if not entry.get("enabled", True):
            continue

        sched = entry.get("schedule", "daily")
        sched_time = entry.get("time", "08:00")

        if sched == "daily":
            schedule_lib.every().day.at(sched_time).do(executor.run_automation, entry)
        elif sched == "hourly":
            schedule_lib.every().hour.do(executor.run_automation, entry)
        elif "minute" in sched.lower():
            try:
                minutes = int(sched.split()[1])
                schedule_lib.every(minutes).minutes.do(executor.run_automation, entry)
            except (IndexError, ValueError):
                logger.warning(f"Unrecognized schedule for {entry['id']}: {sched}")
        else:
            logger.warning(f"Unrecognized schedule type for {entry['id']}: {sched}")


def _scheduler_loop() -> None:
    last_reload = 0.0
    while not _scheduler_stop.is_set():
        if time.time() - last_reload > RELOAD_INTERVAL_SECONDS:
            _register_jobs()
            last_reload = time.time()
        schedule_lib.run_pending()
        time.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=_scheduler_loop, daemon=True)
    thread.start()
    logger.info("Scheduler thread started")
    yield
    _scheduler_stop.set()


app = FastAPI(title="automations", lifespan=lifespan)


def _to_out(entry: dict, name: str, source: str) -> AutomationOut:
    last_run = runs.get_last_run(entry["id"])
    return AutomationOut(
        **entry,
        name=name,
        source=source,
        last_run_status=last_run["status"] if last_run else None,
        last_run_at=last_run["started_at"] if last_run else None,
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "automations"}


@app.get("/automations", response_model=list[AutomationOut])
def list_automations():
    configured = {e["id"]: e for e in store.get_schedules()}
    out = []

    for entry_id, entry in configured.items():
        name = entry_id
        if entry.get("type") == "script":
            for d in discovery.discover_scripts():
                if d["script"] == entry.get("script"):
                    name = d["name"]
                    break
        out.append(_to_out(entry, name, "config"))

    # Scripts that exist on disk but have no config.yaml entry yet.
    for d in discovery.discover_scripts():
        script_id = d["script"].replace("/", "_").replace(".py", "")
        if any(e.get("script") == d["script"] for e in configured.values()):
            continue
        placeholder = {
            "id": script_id,
            "type": "script",
            "enabled": False,
            "schedule": "daily",
            "time": "08:00",
            "script": d["script"],
            "api_call": None,
        }
        out.append(_to_out(placeholder, d["name"], "discovered"))

    return out


@app.get("/automations/{automation_id}", response_model=AutomationOut)
def get_automation(automation_id: str):
    entry = store.get_entry(automation_id)
    if not entry:
        raise HTTPException(404, "Automation not found")
    return _to_out(entry, entry.get("id"), "config")


@app.post("/automations", response_model=AutomationOut)
def create_automation(body: CreateApiCallAutomation):
    if store.get_entry(body.id):
        raise HTTPException(409, "An automation with this id already exists")

    entry = {
        "id": body.id,
        "type": "api_call",
        "enabled": body.enabled,
        "schedule": body.schedule,
        "time": body.time,
        "script": None,
        "api_call": body.api_call.model_dump(),
    }
    store.upsert_entry(entry, f"Add automation: {body.name}")
    return _to_out(entry, body.name, "config")


@app.patch("/automations/{automation_id}", response_model=AutomationOut)
def update_automation(automation_id: str, body: UpdateAutomation):
    entry = store.get_entry(automation_id)
    if not entry:
        # Allow "adopting" a discovered-but-unconfigured script by patching it.
        discovered = next(
            (d for d in discovery.discover_scripts() if d["script"].replace("/", "_").replace(".py", "") == automation_id),
            None,
        )
        if not discovered:
            raise HTTPException(404, "Automation not found")
        entry = {
            "id": automation_id,
            "type": "script",
            "enabled": False,
            "schedule": "daily",
            "time": "08:00",
            "script": discovered["script"],
            "api_call": None,
        }

    updates = body.model_dump(exclude_unset=True)
    if "api_call" in updates and updates["api_call"] is not None:
        updates["api_call"] = body.api_call.model_dump()
    entry.update(updates)

    store.upsert_entry(entry, f"Update automation: {automation_id}")
    return _to_out(entry, entry.get("id"), "config")


@app.delete("/automations/{automation_id}")
def delete_automation(automation_id: str):
    if not store.delete_entry(automation_id, f"Remove automation: {automation_id}"):
        raise HTTPException(404, "Automation not found in config (nothing to remove)")
    return {"ok": True}


@app.post("/automations/{automation_id}/run")
def run_automation_now(automation_id: str):
    entry = store.get_entry(automation_id)
    if not entry:
        raise HTTPException(404, "Automation not found (must be configured, not just discovered)")

    thread = threading.Thread(target=executor.run_automation, args=(entry, "manual"), daemon=True)
    thread.start()
    return {"ok": True, "message": "Run started"}


@app.get("/runs")
def list_runs(automation_id: str | None = None, limit: int = 50):
    return runs.get_runs(automation_id, limit)
