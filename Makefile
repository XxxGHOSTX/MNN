.PHONY: help install lint test smoke build run compose-up compose-down clean fmt

# Default target
help:
	@echo "MNN Pipeline - Makefile Targets"
	@echo "================================"
	@echo "install        - Install Python dependencies (optionally in venv)"
	@echo "lint           - Run linting (py_compile on all Python sources)"
	@echo "test           - Run test suite with pytest"
	@echo "smoke          - Run Docker smoke test (build, run, test, cleanup)"
	@echo "build          - Build Docker image"
	@echo "run            - Run Docker container (single instance)"
	@echo "compose-up     - Start services with docker compose"
	@echo "compose-down   - Stop services with docker compose"
	@echo "clean          - Clean build artifacts and caches"
	@echo "fmt            - Format code (stub - no formatter configured)"

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	@if [ -n "$$VIRTUAL_ENV" ]; then \
		echo "Using existing virtual environment: $$VIRTUAL_ENV"; \
		pip install -r requirements.txt; \
	elif [ -d "venv" ]; then \
		echo "Using existing venv directory"; \
		. venv/bin/activate && pip install -r requirements.txt; \
	else \
		echo "Installing in current Python environment"; \
		pip install -r requirements.txt; \
	fi
	@echo "Installation complete."

# Lint Python sources
lint:
	@echo "Linting Python sources..."
	@python -m compileall .
	@python -m py_compile api.py
	@python -m py_compile main.py
	@python -m py_compile middleware.py
	@python -m py_compile weight_encryptor.py
	@python -m py_compile manual_validation.py
	@python -m py_compile config.py
	@python -m py_compile logging_config.py
	@python -m py_compile security.py
	@find mnn_pipeline -name "*.py" -exec python -m py_compile {} +
	@find tests -name "*.py" -exec python -m py_compile {} +
	@echo "Linting complete - no syntax errors found."

# Run tests
test:
	@echo "Running test suite..."
	@python -m pytest
	@echo "Tests complete."

# Run Docker smoke test
smoke:
	@echo "Running Docker smoke test..."
	@bash -c 'set -euo pipefail; \
	echo "Building Docker image..."; \
	docker build -t mnn:local . && \
	echo "Starting container..."; \
	docker run --rm -d -p 8000:8000 --name mnn_api mnn:local && \
	echo "Waiting for container to be ready..."; \
	healthy=false; \
	for i in {1..30}; do \
		if curl -s http://localhost:8000/health > /dev/null 2>&1; then \
			echo "API is healthy!"; \
			healthy=true; \
			break; \
		fi; \
		echo "Attempt $$i/30: Waiting for API..."; \
		sleep 1; \
	done; \
	if [ "$$healthy" = "false" ]; then \
		echo "ERROR: API did not become healthy after 30 attempts"; \
		docker stop mnn_api || true; \
		exit 1; \
	fi && \
	echo "Testing API endpoint..."; \
	response=$$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/query \
		-H "Content-Type: application/json" \
		-d "{\"query\":\"hello\"}") && \
	body=$$(echo "$$response" | head -n -1) && \
	status=$$(echo "$$response" | tail -n 1) && \
	echo "Response: $$body" && \
	echo "Status: $$status" && \
	if [ "$$status" != "200" ]; then \
		echo "ERROR: Expected status 200, got $$status"; \
		docker stop mnn_api; \
		exit 1; \
	fi && \
	echo "Stopping container..."; \
	docker stop mnn_api && \
	echo "Smoke test passed!"'

# Build Docker image
build:
	@echo "Building Docker image..."
	docker build -t mnn:local .
	@echo "Docker build complete."

# Run Docker container
run:
	@echo "Running Docker container..."
	@echo "Container will be available at http://localhost:8000"
	@echo "Press Ctrl+C to stop"
	docker run --rm -p 8000:8000 --name mnn-pipeline mnn:local

# Start docker-compose services
compose-up:
	@echo "Starting services with docker compose..."
	docker compose up -d
	@echo "Services started. API available at http://localhost:8000"
	@echo "Use 'make compose-down' to stop services."

# Stop docker-compose services
compose-down:
	@echo "Stopping services with docker compose..."
	docker compose down
	@echo "Services stopped."

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts and caches..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf build/ dist/ .coverage htmlcov/ 2>/dev/null || true
	@echo "Clean complete."

# Format code (stub)
fmt:
	@echo "Code formatting stub - no formatter configured."
	@echo "To add formatting, install black or ruff and update this target."
