#!/bin/bash

echo "⚠️  WARNING: This will delete ALL data in the database!"
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Cancelled"
    exit 1
fi

echo "🗑️  Dropping all tables..."
docker compose exec api alembic downgrade base

echo "📊 Creating tables..."
docker compose exec api alembic upgrade head

echo "🌱 Seeding data..."
docker compose exec api python  scripts/seed_data.py
docker compose exec api python  scripts/seed_warehouse_data.py
docker compose exec api python  scripts/seed_production_data.py
docker compose exec api python  scripts/seed_sales_data.py
docker compose exec api python  scripts/seed_finance_data.py
docker compose exec api python  scripts/seed_hr_data.py
docker compose exec api python  scripts/seed_maintenance_data.py

echo "✅ Database reset complete!"