FROM python:3.10-slim

WORKDIR /app

RUN pip install poetry==1.8.5 && \
    poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock* ./

RUN poetry install --only main --no-interaction --no-ansi

COPY . .

CMD ["python", "runner.py", "--scheduler"]
