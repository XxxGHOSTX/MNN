.PHONY: help setup install lint test verify smoke build run run-docker compose-up compose-down clean fmt cpp-deterministic reproducibility-check

DETERMINISTIC_CXXFLAGS=-std=c++17 -O2 -fno-fast-math -ffp-contract=off -fno-common

# Default target
help:
	@echo "MNN Pipeline - Makefile Targets"
	@echo "================================"
	@echo "setup          - Provision the environment (install dependencies)"
	@echo "install        - Install Python dependencies (optionally in venv)"
	@echo "lint           - Run linting (py_compile on all Python sources)"
	@echo "test           - Run test suite with pytest"
	@echo "verify         - Full verification: lint + test + C++ sanity compile"
	@echo "smoke          - Run Docker smoke test (build, run, test, cleanup)"
	@echo "build          - Build Docker image"
	@echo "run            - Start the API server locally (Ctrl+C to stop)"
	@echo "run-docker     - Run API server in Docker container"
	@echo "compose-up     - Start services with docker compose"
	@echo "compose-down   - Stop services with docker compose"
	@echo "cpp-deterministic - Compile C++ core with deterministic flags"
	@echo "reproducibility-check - Run deterministic output and architecture artifact checks"
	@echo "clean          - Clean build artifacts and caches"
	@echo "fmt            - Format code (stub - no formatter configured)"

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
	@python -m compileall . -x '^\./frontend/'
	@python -m py_compile api.py
	@python -m py_compile main.py
	@python -m py_compile middleware.py
	@python -m py_compile weight_encryptor.py
	@python -m py_compile manual_validation.py
	@python -m py_compile config.py
	@python -m py_compile logging_config.py
	@python -m py_compile security.py
	@find mnn -name "*.py" -exec python -m py_compile {} +
	@find mnn_pipeline -name "*.py" -exec python -m py_compile {} +
	@find tests -name "*.py" -exec python -m py_compile {} +
	@find tools -name "*.py" -exec python -m py_compile {} +
	@echo "Linting complete - no syntax errors found."

# Full verification: lint + test + C++ sanity compile
verify: lint test
	@echo "Running C++ core sanity compile..."
	@g++ $(DETERMINISTIC_CXXFLAGS) -Iinclude -c src/mnn_core.cpp -o /tmp/mnn_core_sanity.o
	@rm -f /tmp/mnn_core_sanity.o
	@echo "C++ sanity compile passed."
	@echo "Running verification agent..."
	@python -m tools.verify
	@echo "Verification complete."

cpp-deterministic:
	@echo "Compiling C++ core with deterministic flags..."
	@g++ $(DETERMINISTIC_CXXFLAGS) -Iinclude -c src/mnn_core.cpp -o /tmp/mnn_core_deterministic.o
	@rm -f /tmp/mnn_core_deterministic.o
	@echo "Deterministic C++ compile passed."

reproducibility-check:
	@echo "Running deterministic output check..."
	@python tools/reproducibility_check.py --query "deterministic systems"
	@echo "Generating architecture artifacts..."
	@python tools/generate_architecture_artifacts.py
	@echo "Reproducibility checks complete."

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
	for i in {1..30}; do \
		if curl -s http://localhost:8000/health > /dev/null 2>&1; then \
			echo "API is healthy!"; \
			break; \
		fi; \
		echo "Attempt $$i/30: Waiting for API..."; \
		sleep 1; \
	done && \
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
	@rm -rf build/ dist/ .coverage htmlcov/ 2>/dev/null || true
	@echo "Clean complete."

# Format code (stub)
fmt:
	@echo "Code formatting stub - no formatter configured."
	@echo "To add formatting, install black or ruff and update this target."
