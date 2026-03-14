# Production-ready Dockerfile for MNN Pipeline FastAPI service
FROM python:3.12.8-slim-bookworm

LABEL org.opencontainers.image.created=1970-01-01T00:00:00Z

# Build arguments for reproducible builds and optional configuration
ARG SOURCE_DATE_EPOCH=0
ARG THALOS_DB_DSN=""
ARG THALOS_DB_CONNECT_TIMEOUT="10"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH} \
    THALOS_DB_DSN=${THALOS_DB_DSN} \
    THALOS_DB_CONNECT_TIMEOUT=${THALOS_DB_CONNECT_TIMEOUT}

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY --chown=root:root requirements.txt .

# Install Python dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY --chown=root:root api.py .
COPY --chown=root:root main.py .
COPY --chown=root:root middleware.py .
COPY --chown=root:root weight_encryptor.py .
COPY --chown=root:root thalos_db_schema.sql .
COPY --chown=root:root manual_validation.py .
COPY --chown=root:root config.py .
COPY --chown=root:root logging_config.py .
COPY --chown=root:root security.py .
COPY --chown=root:root metrics.py .
COPY --chown=root:root feedback.py .
COPY --chown=root:root auth_utils.py .
COPY --chown=root:root infra_status.py .

# Copy mnn_pipeline directory
COPY --chown=root:root mnn_pipeline/ ./mnn_pipeline/

# Copy mnn package
COPY --chown=root:root mnn/ ./mnn/

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: run uvicorn on all interfaces
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
