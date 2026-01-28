"""Deploy automations to GCP Cloud Run."""

import argparse
import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "api-gateway-485017")
REGION = os.getenv("GCP_REGION", "us-central1")
IMAGE_URL = f"{REGION}-docker.pkg.dev/{PROJECT_ID}/automations/automations:latest"
AUTOMATION_FOLDERS = ["scheduled", "triggered", "manual"]


def parse_frontmatter(file_path: Path) -> dict[str, Any] | None:
    """Extract YAML frontmatter from a Python file's docstring."""
    content = file_path.read_text(encoding="utf-8")
    match = re.search(r'^"""[\s]*---\s*(.*?)\s*---[\s]*"""', content, re.DOTALL)
    
    if not match:
        return None
    
    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        print(f"Error parsing frontmatter in {file_path}: {e}")
        return None


def discover_automations() -> list[dict[str, Any]]:
    """Scan folders and discover all automations with valid frontmatter."""
    automations = []
    base_path = Path(__file__).parent
    
    for folder in AUTOMATION_FOLDERS:
        folder_path = base_path / folder
        if not folder_path.exists():
            continue
        
        for py_file in folder_path.glob("*.py"):
            if py_file.name.startswith("_") or py_file.name == "handler.py":
                continue
            
            frontmatter = parse_frontmatter(py_file)
            if frontmatter and frontmatter.get("enabled", True):
                automations.append({
                    "file": str(py_file.relative_to(base_path)),
                    "folder": folder,
                    **frontmatter,
                })
    
    return automations


def sync_scheduled(automation: dict, dry_run: bool = False) -> None:
    """Create/update Cloud Run Job + Cloud Scheduler."""
    from google.cloud import run_v2
    from google.cloud import scheduler
    
    name = automation["name"]
    schedule = automation["schedule"]
    timezone = automation.get("timezone", "America/New_York")
    file_path = automation["file"]
    
    job_name = f"projects/{PROJECT_ID}/locations/{REGION}/jobs/{name}"
    scheduler_name = f"projects/{PROJECT_ID}/locations/{REGION}/jobs/{name}-trigger"
    
    print(f"  → Job: {name} | Schedule: {schedule} ({timezone})")
    
    if dry_run:
        return
    
    jobs_client = run_v2.JobsClient()
    job = run_v2.Job(
        template=run_v2.ExecutionTemplate(
            template=run_v2.TaskTemplate(
                containers=[run_v2.Container(
                    image=IMAGE_URL,
                    command=["python"],
                    args=["runner.py", file_path],
                )],
                max_retries=1,
            )
        )
    )
    
    try:
        jobs_client.get_job(name=job_name)
        jobs_client.update_job(job=job, allow_missing=True).result()
        print(f"    ✓ Updated job")
    except Exception:
        jobs_client.create_job(
            parent=f"projects/{PROJECT_ID}/locations/{REGION}",
            job=job,
            job_id=name,
        ).result()
        print(f"    ✓ Created job")
    
    scheduler_client = scheduler.CloudSchedulerClient()
    scheduler_job = scheduler.Job(
        name=scheduler_name,
        schedule=schedule,
        time_zone=timezone,
        http_target=scheduler.HttpTarget(
            uri=f"https://{REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/{PROJECT_ID}/jobs/{name}:run",
            http_method=scheduler.HttpMethod.POST,
            oauth_token=scheduler.OAuthToken(
                service_account_email=f"{PROJECT_ID}@appspot.gserviceaccount.com",
            ),
        ),
    )
    
    try:
        scheduler_client.get_job(name=scheduler_name)
        scheduler_client.update_job(job=scheduler_job)
        print(f"    ✓ Updated scheduler")
    except Exception:
        scheduler_client.create_job(
            parent=f"projects/{PROJECT_ID}/locations/{REGION}",
            job=scheduler_job,
        )
        print(f"    ✓ Created scheduler")


def sync_triggered(automations: list[dict], dry_run: bool = False) -> None:
    """Create/update Cloud Run Service for triggered automations."""
    from google.cloud import run_v2
    
    if not automations:
        return
    
    service_name = "automations-triggered"
    print(f"\n[triggered] Service: {service_name}")
    for auto in automations:
        print(f"  → Route: {auto.get('path', '/' + auto['name'])}")
    
    if dry_run:
        return
    
    services_client = run_v2.ServicesClient()
    service = run_v2.Service(
        template=run_v2.RevisionTemplate(
            containers=[run_v2.Container(
                image=IMAGE_URL,
                command=["gunicorn"],
                args=["--bind", "0.0.0.0:8080", "triggered.handler:app"],
                ports=[run_v2.ContainerPort(container_port=8080)],
            )],
        ),
    )
    
    try:
        services_client.update_service(service=service, allow_missing=True).result()
        print(f"    ✓ Updated service")
    except Exception:
        services_client.create_service(
            parent=f"projects/{PROJECT_ID}/locations/{REGION}",
            service=service,
            service_id=service_name,
        ).result()
        print(f"    ✓ Created service")


def sync_manual(automation: dict, dry_run: bool = False) -> None:
    """Create/update Cloud Run Job (no scheduler)."""
    from google.cloud import run_v2
    
    name = automation["name"]
    file_path = automation["file"]
    
    print(f"  → Job: {name} (manual)")
    
    if dry_run:
        return
    
    jobs_client = run_v2.JobsClient()
    job = run_v2.Job(
        template=run_v2.ExecutionTemplate(
            template=run_v2.TaskTemplate(
                containers=[run_v2.Container(
                    image=IMAGE_URL,
                    command=["python"],
                    args=["runner.py", file_path],
                )],
                max_retries=1,
            )
        )
    )
    
    try:
        jobs_client.update_job(job=job, allow_missing=True).result()
        print(f"    ✓ Updated job")
    except Exception:
        jobs_client.create_job(
            parent=f"projects/{PROJECT_ID}/locations/{REGION}",
            job=job,
            job_id=name,
        ).result()
        print(f"    ✓ Created job")


def cmd_sync(dry_run: bool = False) -> None:
    """Sync all automations to GCP."""
    print(f"{'[DRY RUN] ' if dry_run else ''}Syncing to {PROJECT_ID}/{REGION}")
    print(f"Image: {IMAGE_URL}\n")
    
    automations = discover_automations()
    if not automations:
        print("No automations found.")
        return
    
    scheduled = [a for a in automations if a.get("type") == "scheduled"]
    triggered = [a for a in automations if a.get("type") == "triggered"]
    manual = [a for a in automations if a.get("type") == "manual"]
    
    if scheduled:
        print(f"[scheduled] {len(scheduled)} automation(s)")
        for auto in scheduled:
            sync_scheduled(auto, dry_run)
    
    if triggered:
        sync_triggered(triggered, dry_run)
    
    if manual:
        print(f"\n[manual] {len(manual)} automation(s)")
        for auto in manual:
            sync_manual(auto, dry_run)
    
    print("\n✓ Done!")


def cmd_status() -> None:
    """List discovered automations."""
    automations = discover_automations()
    if not automations:
        print("No automations found.")
        return
    
    for auto in automations:
        schedule = f" | {auto['schedule']}" if auto.get("schedule") else ""
        print(f"[{auto['folder']}] {auto['name']}{schedule}")
        print(f"         {auto['file']}")


def main():
    parser = argparse.ArgumentParser(description="Deploy automations to GCP")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    sync_parser = subparsers.add_parser("sync", help="Sync to GCP")
    sync_parser.add_argument("--dry-run", action="store_true")
    
    subparsers.add_parser("status", help="List automations")
    
    args = parser.parse_args()
    
    if args.command == "sync":
        cmd_sync(dry_run=args.dry_run)
    elif args.command == "status":
        cmd_status()


if __name__ == "__main__":
    main()
