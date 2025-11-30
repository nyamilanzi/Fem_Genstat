.PHONY: help dev backend frontend test lint build clean install

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

dev: ## Start both frontend and backend in development mode
	@echo "Starting development environment..."
	@make backend &
	@make frontend

backend: ## Start FastAPI backend
	@echo "Starting backend server..."
	cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

frontend: ## Start Next.js frontend
	@echo "Starting frontend server..."
	cd frontend && npm run dev

test: ## Run all tests
	@echo "Running backend tests..."
	cd backend && python -m pytest tests/ -v
	@echo "Running frontend tests..."
	cd frontend && npm test

lint: ## Run linting for both frontend and backend
	@echo "Linting backend..."
	cd backend && ruff check . && ruff format --check .
	@echo "Linting frontend..."
	cd frontend && npm run lint

build: ## Build both frontend and backend
	@echo "Building frontend..."
	cd frontend && npm run build
	@echo "Backend is ready to run with uvicorn"

install: ## Install dependencies
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

clean: ## Clean build artifacts
	@echo "Cleaning frontend build..."
	cd frontend && rm -rf .next
	@echo "Cleaning Python cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start with Docker Compose
	docker-compose up

docker-down: ## Stop Docker Compose
	docker-compose down

