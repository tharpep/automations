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

# Default command (override in docker-compose or when running)
CMD ["python", "-m", "scripts"]
