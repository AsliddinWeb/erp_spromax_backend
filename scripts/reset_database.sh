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
docker compose exec api python scripts/seed_all_data.py

echo "✅ Database reset complete!"