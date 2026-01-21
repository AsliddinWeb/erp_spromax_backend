.PHONY: help build up down logs shell migrate seed clean restart ps

help:
	@echo "Available commands:"
	@echo "  make build     - Build Docker images"
	@echo "  make up        - Start all services"
	@echo "  make down      - Stop all services"
	@echo "  make restart   - Restart all services"
	@echo "  make logs      - View API logs"
	@echo "  make ps        - Show running containers"
	@echo "  make shell     - Access API container shell"
	@echo "  make db-shell  - Access database shell"
	@echo "  make migrate   - Run database migrations"
	@echo "  make seed      - Seed database with all data"
	@echo "  make clean     - Remove all containers and volumes"

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f api

ps:
	docker compose ps

shell:
	docker compose exec api bash

db-shell:
	docker compose exec db psql -U promax_user -d promax_erp

migrate:
	docker compose exec api alembic upgrade head

seed:
	@echo "🌱 Seeding all data..."
	@docker compose exec api python scripts/seed_all_data.py

clean:
	docker compose down -v
	docker system prune -f