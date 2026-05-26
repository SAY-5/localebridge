FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN pip install --no-cache-dir poetry==2.1.3 \
    && poetry config virtualenvs.create false

COPY pyproject.toml ./
COPY src ./src

RUN poetry install --only main --no-interaction --no-ansi

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "localebridge.api:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
