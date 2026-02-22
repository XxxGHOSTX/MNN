# Lightweight build variant for MNN Pipeline
# Uses the same base image and structure as the root Dockerfile
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt

COPY api.py main.py middleware.py weight_encryptor.py config.py \
     logging_config.py security.py metrics.py feedback.py ./
COPY thalos_db_schema.sql .
COPY mnn_pipeline/ ./mnn_pipeline/
COPY mnn/ ./mnn/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
