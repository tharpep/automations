FROM python:3.10-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry==1.7.1 && \
    poetry config virtualenvs.create false

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Default command - start scheduler
# Override in docker-compose.yml or when running:
#   docker run <image> python scripts/runner.py scripts/notifications/email_check.py
CMD ["python", "scripts/runner.py", "--scheduler"]
