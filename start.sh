#!/bin/bash

echo "🚀 Starting S PROMAX PLAST ERP..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your settings"
    exit 1
fi

# Build and start containers
echo "📦 Building containers..."
docker compose build

echo "🔄 Starting services..."
docker compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 15

# Check if services are running
if docker compose ps | grep -q "promax_api.*Up"; then
    echo "✅ Services are up!"
    
    # Run migrations
    echo "📊 Running database migrations..."
    docker compose exec api alembic upgrade head
    
    # Ask if user wants to seed data
    read -p "🌱 Do you want to seed initial data? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🌱 Seeding database..."
        make seed
    fi
    
    echo ""
    echo "✨ ERP System is ready!"
    echo "📚 API Documentation: http://localhost:8000/docs"
    echo "🔍 Health Check: http://localhost:8000/health"
    echo ""
    echo "Useful commands:"
    echo "  make logs       - View API logs"
    echo "  make ps         - Show running containers"
    echo "  make shell      - Access API container"
    echo "  make db-shell   - Access database"
    echo "  make down       - Stop all services"
    echo ""
else
    echo "❌ Failed to start services"
    docker compose logs
    exit 1
fi