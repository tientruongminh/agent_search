FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace/apps/api

RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /workspace/apps/api/pyproject.toml
COPY alembic.ini /workspace/apps/api/alembic.ini
COPY alembic /workspace/apps/api/alembic
COPY app /workspace/apps/api/app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

EXPOSE 8000

