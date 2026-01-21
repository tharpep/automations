# Automations

One place for all scripts, shared utilities, single config.

## Structure

- `scripts/` - Automation scripts organized by purpose
- `utils/` - Shared utilities
- `config/` - Configuration files

## Setup

```bash
# Install dependencies
poetry install

# Run a script
poetry run python scripts/<category>/<script_name>.py

# Or with Docker
docker-compose up
```

## Scripts

_No scripts yet. Add scripts to `scripts/<category>/` and update this section._

## Configuration

Edit `config/config.yaml` to customize behavior.
