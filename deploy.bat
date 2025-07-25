@echo off
echo 🚀 ENTERPRISE COWORKING PLATFORM - PRODUCTION DEPLOYMENT

REM Check if .env exists
if not exist .env (
    echo ❌ ERROR: .env file not found
    echo 📋 Please copy .env.example to .env and configure with your values
    pause
    exit /b 1
)

echo 🔧 Building production containers...
docker-compose -f docker-compose.prod.yml build --no-cache

echo 🗄️ Starting database and cache...
docker-compose -f docker-compose.prod.yml up -d db redis

echo ⏳ Waiting for database to be ready...
timeout /t 30 /nobreak

echo 🔄 Running database migrations...
docker-compose -f docker-compose.prod.yml run --rm web python manage.py migrate

echo 🚀 Starting all production services...
docker-compose -f docker-compose.prod.yml up -d

echo ✅ Deployment complete!
echo 🌐 Platform: https://your-domain.com
echo 📊 Health: https://your-domain.com/health/
echo 🔧 Admin: https://your-domain.com/admin/

echo 🔍 Service status:
docker-compose -f docker-compose.prod.yml ps

pause