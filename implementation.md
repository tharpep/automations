# Dynamic Automations Infrastructure

Config-driven automation deployment to GCP. Single image, dynamic job creation, three automation types.

## Automation Types

| Type | Trigger | GCP Resource | Folder |
|------|---------|--------------|--------|
| **Scheduled** | Cron | Cloud Run Job + Cloud Scheduler | `scheduled/` |
| **Triggered** | HTTP/Pub/Sub | Cloud Run Service (HTTP endpoint) | `triggered/` |
| **Manual** | CLI/Dashboard | Cloud Run Job (no scheduler) | `manual/` |

---

## Architecture

```
┌────────────────────┐      push      ┌─────────────────────────┐
│  GitHub Repo       │ ─────────────▶ │  GitHub Actions         │
│  automations/      │                │  1. Build image         │
│                    │                │  2. Push to Artifact    │
│  scheduled/*.py    │ ◀─ frontmatter │     Registry            │
│  triggered/*.py    │    metadata    │  3. deploy.py sync      │
│  manual/*.py       │                └─────────────────────────┘
└────────────────────┘                           │
                                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  GCP (project: api-gateway)                                     │
│                                                                 │
│  Scheduled:                                                     │
│  ┌─────────────────┐         ┌─────────────────────────┐       │
│  │ Cloud Scheduler │ ──────▶ │ Cloud Run Job           │       │
│  └─────────────────┘         └─────────────────────────┘       │
│                                                                 │
│  Triggered:                                                     │
│  ┌─────────────────┐         ┌─────────────────────────┐       │
│  │ External Event  │ ──────▶ │ Cloud Run Service       │       │
│  │ (webhook, etc)  │   HTTP  │ (always listening)      │       │
│  └─────────────────┘         └─────────────────────────┘       │
│                                                                 │
│  Manual:                                                        │
│  ┌─────────────────┐         ┌─────────────────────────┐       │
│  │ CLI / Dashboard │ ──────▶ │ Cloud Run Job           │       │
│  │ (you trigger)   │         │ (no scheduler)          │       │
│  └─────────────────┘         └─────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Frontmatter Schema

Each script declares its config in docstring frontmatter:

**Scheduled:**
```python
"""
---
name: daily-summary
type: scheduled
schedule: "0 9 * * *"
timezone: America/New_York
enabled: true
---
"""
```

**Triggered:**
```python
"""
---
name: github-webhook
type: triggered
trigger: http
path: /webhooks/github
enabled: true
---
"""
```

**Manual:**
```python
"""
---
name: refresh-cache
type: manual
description: Force refresh all cached data
enabled: true
---
"""
```

---

## New Files

### deploy.py

Scans all folders, reads frontmatter, syncs to GCP based on type:

| Type | Action |
|------|--------|
| `scheduled` | Create Cloud Run Job + Cloud Scheduler |
| `triggered` | Create Cloud Run Service with HTTP endpoint |
| `manual` | Create Cloud Run Job only (no scheduler) |

Commands:
- `python deploy.py sync` — full sync
- `python deploy.py sync --dry-run` — preview only
- `python deploy.py status` — list deployed resources

### triggered/handler.py

Lightweight Flask server that routes to triggered scripts. Deployed as single Cloud Run Service.

### .github/workflows/deploy.yml

Mirrors api-gateway pattern. Builds image, pushes to Artifact Registry, runs `deploy.py sync`.

---

## Dependencies to Add

```toml
google-cloud-run = "^0.10"
google-cloud-scheduler = "^2.13"
flask = "^3.0"
gunicorn = "^21.0"
```

---

## One-Time GCP Setup

```bash
gcloud artifacts repositories create automations \
  --repository-format=docker \
  --location=us-central1 \
  --project=api-gateway-485017
```
