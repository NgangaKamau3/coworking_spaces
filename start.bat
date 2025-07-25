@echo off
echo Starting Coworking Platform...

REM Build and start containers
docker-compose up --build -d

REM Wait for database
echo Waiting for database...
timeout /t 15 /nobreak

REM Install missing dependencies
echo Installing dependencies...
docker-compose exec web pip install djangorestframework-gis==1.0

REM Run migrations
echo Running migrations...
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

REM Create superuser
echo Creating superuser...
docker-compose exec web python manage.py shell -c "from django.contrib.auth import get_user_model; from apps.authentication.models import UserProfile; User = get_user_model(); user = User.objects.create_superuser('admin@coworking.com', 'admin@coworking.com', 'admin123') if not User.objects.filter(email='admin@coworking.com').exists() else None; UserProfile.objects.create(user=user, full_name='Admin User', user_type_code='PartnerAdmin') if user else None; print('Superuser created: admin@coworking.com / admin123')"

echo Platform ready at http://localhost:8000
echo Admin panel at http://localhost:8000/admin
echo API docs at http://localhost:8000/api/v1/
pause