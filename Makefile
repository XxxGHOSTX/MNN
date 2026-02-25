.PHONY: help setup install lint test verify smoke build run run-docker compose-up compose-down clean fmt format

# Default target
help:
	@echo "MNN Pipeline - Makefile Targets"
	@echo "================================"
	@echo "setup          - Provision the environment (install dependencies)"
	@echo "install        - Install Python dependencies (optionally in venv)"
	@echo "fmt/format      - Format code with black and isort"
	@echo "lint           - Run linting (pre-commit run --all-files)"
	@echo "test           - Run test suite with coverage"
	@echo "verify         - Full verification: lint + test + C++ sanity compile"
	@echo "smoke          - Run Docker smoke test (build, run, test, cleanup)"
	@echo "build          - Build Docker image"
	@echo "run            - Start the API server locally (Ctrl+C to stop)"
	@echo "run-docker     - Run API server in Docker container"
	@echo "compose-up     - Start services with docker compose"
	@echo "compose-down   - Stop services with docker compose"
	@echo "clean          - Clean build artifacts and caches"
	@echo "fmt            - Alias for fmt/format target (see above)"

# Provision the environment (deterministic setup from a clean clone)
setup: install
	@if [ ! -f .env ]; then \
		echo "Creating .env from .env.example..."; \
		cp .env.example .env; \
		echo ".env created. Review and edit before use."; \
	else \
		echo ".env already exists, skipping copy."; \
	fi
	@echo "Setup complete. Run 'make verify' to validate, 'make run' to start."

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
	@pre-commit run --all-files
	@echo "Linting complete."

# Full verification: lint + test + C++ sanity compile
verify: lint test
	@echo "Running C++ core sanity compile..."
	@g++ -std=c++17 -Iinclude -c src/mnn_core.cpp -o /tmp/mnn_core_sanity.o
	@rm -f /tmp/mnn_core_sanity.o
	@echo "C++ sanity compile passed."
	@echo "Verification complete."

# Run tests
test:
	@echo "Running test suite..."
	@coverage run -m pytest
	@coverage report || true
	@echo "Tests complete."

# Run Docker smoke test
smoke:
	@echo "Running Docker smoke test..."
	@docker build -t mnn:local .
	@docker run -d --name mnn_smoke -e THALOS_DB_DSN="$$THALOS_DB_DSN" mnn:local
	@sleep 10
	@docker logs mnn_smoke
	@docker stop mnn_smoke || true
	@docker rm mnn_smoke || true
	@echo "Smoke test complete."

# Build Docker image
build:
	@echo "Building Docker image..."
	docker build -t mnn:local .
	@echo "Docker build complete."

# Start the API server locally (runs until Ctrl+C)
run:
	@echo "Starting MNN API server locally..."
	@echo "API available at http://localhost:8000"
	@echo "Press Ctrl+C to stop"
	@python -m uvicorn api:app --host 127.0.0.1 --port 8000

# Run Docker container
run-docker:
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
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -f coverage.xml
	@rm -rf build/ dist/ .coverage htmlcov/ 2>/dev/null || true
	@echo "Clean complete."

# Format code with black and isort
fmt format:
	@echo "Formatting code with black and isort..."
	@black --line-length 100 .
	@isort --profile black .
	@echo "Formatting complete."
