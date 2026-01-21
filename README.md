# Automations

One place for all scripts, shared utilities, single config.

## Structure

- `scripts/` - Automation scripts organized by purpose
  - `runner.py` - Script runner and scheduler
- `utils/` - Shared utilities (config loader, logger, scheduler)
- `config/` - Configuration files

## Setup

### Local Development

```bash
# Install dependencies
poetry install

# Run a script once
poetry run python scripts/runner.py scripts/<category>/<script_name>.py

# Start scheduler (runs scripts on schedule from config.yaml)
poetry run python scripts/runner.py --scheduler
```

### Docker Deployment

```bash
# Build and start (runs scheduler by default)
docker-compose up -d

# Run a specific script once
docker-compose run --rm automations python scripts/runner.py scripts/<category>/<script_name>.py

# View logs
docker-compose logs -f
```

## Configuration

1. **config/config.yaml** - Script schedules and settings
2. **.env** - Secrets and API keys (create this file, add to .gitignore)

## Automation Ideas

Potential scripts to build:

### Notifications
- Email monitoring - Get notified when specific emails arrive (from certain senders, keywords, etc.)
- Calendar alerts - Reminders for upcoming events or schedule changes
- Task completion notifications - Alert when tasks are completed or deadlines approach

### Summaries
- Daily summary - AI-generated summary of your day (emails, calendar, tasks)
- Weekly review - Aggregate weekly activity and accomplishments
- Meeting summaries - Auto-summarize calendar events and outcomes

### Data Processing
- File organization - Automatically organize downloads or documents
- Backup automation - Regular backups of important files or data
- Data aggregation - Collect and combine data from multiple sources

### Local Automation
- System monitoring - Track system resources, disk space, etc.
- Application automation - Automate repetitive tasks in local applications
- File watching - Monitor directories and trigger actions on file changes

## How It Works

1. **On-demand**: Run scripts manually with `python scripts/runner.py <script_path>`
2. **Scheduled**: Add schedules to `config/config.yaml`, then run `--scheduler`
3. **Docker**: Container runs scheduler by default, executes scripts based on config

## Adding New Scripts

1. Create script in `scripts/<category>/your_script.py`
2. Include a `main()` function
3. Use `utils.config_loader.load_config()` and `utils.logger.setup_logger()`
4. Add to schedules in `config/config.yaml` if you want it to run automatically
5. Update this README with a description
