# slim cpu-only inference image. mounts an artifacts volume at runtime so the
# image stays small and the same image works for ncf retrains.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# minimal runtime deps; no implicit (server only serves the neural + hybrid)
RUN pip install --no-cache-dir \
      "torch==2.2.*+cpu" --index-url https://download.pytorch.org/whl/cpu || \
    pip install --no-cache-dir "torch==2.2.*"

RUN pip install --no-cache-dir \
      "fastapi>=0.110" \
      "uvicorn[standard]>=0.27" \
      "numpy>=1.26,<2.2" \
      "pandas>=2.2" \
      "pyarrow>=15.0" \
      "scipy>=1.11" \
      "boto3>=1.34"

COPY src/ /app/src/
COPY deploy/serve.py /app/serve.py

# expected at runtime: /app/artifacts/ncf.pt, /app/data/processed/tracks.parquet,
# /app/data/audio_features/dataset.csv
EXPOSE 8000
CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8000"]
