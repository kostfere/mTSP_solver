.PHONY: install run dev test lint format clean help

# Default target
help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies using Poetry"
	@echo "  make run        - Run the FastAPI server"
	@echo "  make dev        - Run the FastAPI server with auto-reload"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linting"
	@echo "  make format     - Format code"
	@echo "  make clean      - Remove cache files"

# Install dependencies
install:
	poetry install

# Run the server
run:
	poetry run uvicorn main:app --host 0.0.0.0 --port 8000

# Run the server with auto-reload for development
dev:
	poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
test:
	poetry run pytest

# Run linting
lint:
	poetry run ruff check .

# Format code
format:
	poetry run ruff format .

# Clean cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
