# Stage 1: Build frontend
FROM node:20-slim AS frontend

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build


# Stage 2: Build backend
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --no-dev --no-install-project

COPY backend/src/ src/
COPY --from=frontend /frontend/dist src/samfhir/static/
RUN uv sync --no-dev


# Stage 3: Runtime
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "samfhir.main:app", "--host", "0.0.0.0", "--port", "8000"]
