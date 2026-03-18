# ─────────────────────────────────────────────────────────────
# HRCE — Developer Makefile
# Usage: make <target>
# ─────────────────────────────────────────────────────────────

.PHONY: help up down restart logs ps build migrate test lint clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ─── Docker ───────────────────────────────────────────────────
up: ## Start all services (detached)
	docker compose up -d

down: ## Stop all services
	docker compose down

restart: ## Restart all services
	docker compose restart

logs: ## Follow logs for all services
	docker compose logs -f

ps: ## Show running containers
	docker compose ps

build: ## Rebuild all Docker images
	docker compose build --no-cache

# ─── Database ─────────────────────────────────────────────────
migrate: ## Run Alembic migrations
	docker compose exec backend alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="your message")
	docker compose exec backend alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback last migration
	docker compose exec backend alembic downgrade -1

# ─── Testing ──────────────────────────────────────────────────
test: ## Run backend tests
	docker compose exec backend pytest tests/ -v

test-local: ## Run backend tests locally (requires local venv)
	cd backend && python -m pytest tests/ -v

# ─── Linting ──────────────────────────────────────────────────
lint: ## Run flake8 + isort on backend
	docker compose exec backend flake8 app/
	docker compose exec backend isort --check-only app/

format: ## Auto-format backend code
	docker compose exec backend black app/
	docker compose exec backend isort app/

# ─── Cleanup ──────────────────────────────────────────────────
clean: ## Remove stopped containers, unused images, volumes
	docker compose down -v --remove-orphans
	docker system prune -f
