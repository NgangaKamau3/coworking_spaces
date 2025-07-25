#!/bin/bash
echo "🚀 ENTERPRISE COWORKING PLATFORM - PRODUCTION DEPLOYMENT"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ ERROR: .env file not found"
    echo "📋 Please copy .env.example to .env and configure with your values"
    exit 1
fi

echo "🔧 Building production containers..."
docker-compose build --no-cache

echo "🗄️ Starting database and cache..."
docker-compose up -d db redis

echo "⏳ Waiting for database to be ready..."
sleep 30

echo "🔄 Running database migrations..."
docker-compose run --rm web python manage.py migrate

echo "🚀 Starting all production services..."
docker-compose up -d

echo "✅ Deployment complete!"
echo "🌐 Platform: https://your-domain.com"
echo "📊 Health: https://your-domain.com/health/"
echo "🔧 Admin: https://your-domain.com/admin/"

echo "🔍 Service status:"
docker-compose ps