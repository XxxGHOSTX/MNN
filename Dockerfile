# Production-ready Dockerfile for MNN Pipeline FastAPI service
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build arguments for optional configuration
ARG THALOS_DB_DSN=""
ARG THALOS_DB_CONNECT_TIMEOUT="10"

# Set environment variables from build args (can be overridden at runtime)
ENV THALOS_DB_DSN=${THALOS_DB_DSN} \
    THALOS_DB_CONNECT_TIMEOUT=${THALOS_DB_CONNECT_TIMEOUT}

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY api.py .
COPY main.py .
COPY middleware.py .
COPY weight_encryptor.py .
COPY thalos_db_schema.sql .
COPY manual_validation.py .

# Copy mnn_pipeline directory
COPY mnn_pipeline/ ./mnn_pipeline/

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Default command: run uvicorn on all interfaces
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
