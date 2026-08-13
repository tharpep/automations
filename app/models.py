from typing import Any, Literal, Optional

from pydantic import BaseModel


class ApiCallConfig(BaseModel):
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = "GET"
    path: str
    payload: Optional[dict[str, Any]] = None
    notify: bool = False
    notify_template: str = "{name} finished: {result}"


class AutomationEntry(BaseModel):
    id: str
    type: Literal["script", "api_call"]
    enabled: bool = True
    schedule: str = "daily"  # "daily" | "hourly" | "every N minutes"
    time: str = "08:00"  # only used when schedule == "daily"

    # type == "script"
    script: Optional[str] = None

    # type == "api_call"
    api_call: Optional[ApiCallConfig] = None


class AutomationOut(AutomationEntry):
    name: str
    source: Literal["config", "discovered"]
    last_run_status: Optional[str] = None
    last_run_at: Optional[float] = None


class CreateApiCallAutomation(BaseModel):
    id: str
    name: str
    enabled: bool = True
    schedule: str = "daily"
    time: str = "08:00"
    api_call: ApiCallConfig


class UpdateAutomation(BaseModel):
    enabled: Optional[bool] = None
    schedule: Optional[str] = None
    time: Optional[str] = None
    api_call: Optional[ApiCallConfig] = None


class RunRecord(BaseModel):
    id: str
    automation_id: str
    started_at: float
    finished_at: Optional[float] = None
    status: Literal["running", "success", "error"]
    error: Optional[str] = None
    triggered_by: Literal["schedule", "manual"] = "schedule"
