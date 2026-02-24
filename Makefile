.PHONY: help build up down logs shell migrate seed-users seed-warehouse seed-production seed-sales seed-finance seed-hr seed-maintenance seed-all clear-db clean restart ps db-shell

help:
	@echo "Available commands:"
	@echo "  make build              - Build Docker images"
	@echo "  make up                 - Start all services"
	@echo "  make down               - Stop all services"
	@echo "  make restart            - Restart all services"
	@echo "  make logs               - View API logs"
	@echo "  make ps                 - Show running containers"
	@echo "  make shell              - Access API container shell"
	@echo "  make db-shell           - Access database shell"
	@echo "  make migrate            - Run database migrations"
	@echo ""
	@echo "Database commands:"
	@echo "  make clear-db           - Clear all data from database (keeps tables)"
	@echo "  make clean              - Remove all containers and volumes"
	@echo ""
	@echo "Seed commands:"
	@echo "  make seed-all           - Run ALL seed scripts in correct order"
	@echo "  make seed-users         - Seed users, roles & permissions"
	@echo "  make seed-warehouse     - Seed warehouse data (suppliers, materials)"
	@echo "  make seed-production    - Seed production data (lines, machines, products)"
	@echo "  make seed-sales         - Seed sales data (customers)"
	@echo "  make seed-finance       - Seed finance data (transaction categories)"
	@echo "  make seed-hr            - Seed HR data (departments, employees)"
	@echo "  make seed-maintenance   - Seed maintenance data (spare parts)"

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

clear-db:
	@echo "🗑️  Clearing database..."
	@docker compose exec -T api python scripts/clear_database.py

seed-users:
	@echo "🌱 Seeding users, roles & permissions..."
	@docker compose exec api python scripts/seed_data.py

seed-warehouse:
	@echo "🌱 Seeding warehouse data..."
	@docker compose exec api python scripts/seed_warehouse_data.py

seed-production:
	@echo "🌱 Seeding production data..."
	@docker compose exec api python scripts/seed_production_data.py

seed-sales:
	@echo "🌱 Seeding sales data..."
	@docker compose exec api python scripts/seed_sales_data.py

seed-finance:
	@echo "🌱 Seeding finance data..."
	@docker compose exec api python scripts/seed_finance_data.py

seed-hr:
	@echo "🌱 Seeding HR data..."
	@docker compose exec api python scripts/seed_hr_data.py

seed-maintenance:
	@echo "🌱 Seeding maintenance data..."
	@docker compose exec api python scripts/seed_maintenance_data.py

seed-all:
	@echo ""
	@echo "🌱 ============================================"
	@echo "🌱 RUNNING ALL SEED SCRIPTS IN ORDER"
	@echo "🌱 ============================================"
	@echo ""
	@$(MAKE) seed-users
	@echo ""
	@$(MAKE) seed-warehouse
	@echo ""
	@$(MAKE) seed-production
	@echo ""
	@$(MAKE) seed-sales
	@echo ""
	@$(MAKE) seed-finance
	@echo ""
	@$(MAKE) seed-hr
	@echo ""
	@$(MAKE) seed-maintenance
	@echo ""
	@echo "✅ ============================================"
	@echo "✅ ALL SEED SCRIPTS COMPLETED SUCCESSFULLY!"
	@echo "✅ ============================================"
	@echo ""

clean:
	docker compose down -v
	docker system prune -f