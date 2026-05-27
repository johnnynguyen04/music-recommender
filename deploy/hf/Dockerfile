# Dockerfile for Hugging Face Spaces (Docker SDK).
# Run target: deploy/serve.py FastAPI. HF Spaces serves on port 7860.

FROM python:3.11-slim

# uv for fast deps install
COPY --from=ghcr.io/astral-sh/uv:0.10.11 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    ARTIFACTS_DIR=/app/artifacts \
    DATA_PROC_DIR=/app/data/processed \
    DATA_AUDIO_CSV=/app/data/audio_features/dataset.csv \
    RESULTS_METRICS=/app/results/metrics \
    FRONTEND_ORIGIN="*"

# HF Spaces wants the app to run as uid 1000
RUN useradd -m -u 1000 app
WORKDIR /app
RUN chown -R app:app /app
USER app

# dependency layer (cached unless pyproject.toml / uv.lock change).
# --no-install-project skips building the local "music-recommender" package
# itself; we just want its dependencies. src/ is imported directly at runtime.
COPY --chown=app:app pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project --extra serve

# code + artifacts + data
COPY --chown=app:app src/ ./src/
COPY --chown=app:app deploy/serve.py ./deploy/serve.py
COPY --chown=app:app artifacts/ ./artifacts/
COPY --chown=app:app data/processed/ ./data/processed/
COPY --chown=app:app data/audio_features/ ./data/audio_features/
COPY --chown=app:app results/metrics/ ./results/metrics/

EXPOSE 7860
CMD ["uvicorn", "deploy.serve:app", "--host", "0.0.0.0", "--port", "7860"]
