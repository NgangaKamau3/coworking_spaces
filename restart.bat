@echo off
echo Restarting Coworking Platform...

REM Stop existing containers
docker-compose down

REM Remove volumes to start fresh
docker-compose down -v

REM Build and start containers
docker-compose up --build -d

REM Wait for services to be ready
echo Waiting for services...
timeout /t 30 /nobreak

REM Check if web service is running
docker-compose ps

REM Wait for web service to be ready
echo Waiting for web service to start...
timeout /t 10 /nobreak

REM Create superuser
echo Creating superuser...
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@coworking.com', 'admin123') if not User.objects.filter(email='admin@coworking.com').exists() else print('User exists')" | docker-compose exec -T web python manage.py shell || echo "Superuser creation skipped"

echo Platform ready at http://localhost:8000
echo Admin panel at http://localhost:8000/admin
echo API docs at http://localhost:8000/api/v1/
pause