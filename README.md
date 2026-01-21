# Automations

One place for all automation scripts, organized by trigger type.

## Structure

```
automations/
├── scheduled/     # Timer-based (cron, daily, hourly)
├── triggered/     # Event-driven (webhooks, external events)
├── manual/        # On-demand only (CLI, dashboard)
├── utils/         # Shared utilities
├── config/        # Configuration files
└── runner.py      # Local dev runner/scheduler
```

## Setup

```bash
# Install dependencies
poetry install

# Run a script once
poetry run python runner.py scheduled/daily_summary.py

# Start scheduler (runs scripts on schedule from config.yaml)
poetry run python runner.py --scheduler
```

## Docker

```bash
# Build and start (runs scheduler by default)
docker-compose up -d

# Run a specific script once
docker-compose run --rm automations python runner.py scheduled/daily_summary.py
```

## Configuration

- `config/config.yaml` — Script schedules and settings
- `.env` — Secrets and API keys

## Adding Automations

1. Create script in appropriate folder (`scheduled/`, `triggered/`, `manual/`)
2. Include a `main()` function
3. Use `utils.config_loader.load_config()` and `utils.logger.setup_logger()`
4. For scheduled scripts, add to `config/config.yaml`

## GCP Deployment

| Folder | Deployment Model |
|--------|-----------------|
| `scheduled/` | Cloud Scheduler → Cloud Run Job |
| `triggered/` | Cloud Functions or Eventarc |
| `manual/` | CLI or one-off Cloud Run Job |
