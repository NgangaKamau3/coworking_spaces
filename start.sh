#!/bin/bash

echo "Starting Coworking Platform..."

# Build and start containers
docker-compose up --build -d

# Wait for database
echo "Waiting for database..."
sleep 10

# Run migrations
echo "Running migrations..."
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

# Create superuser (optional)
echo "Creating superuser..."
docker-compose exec web python manage.py shell -c "
from django.contrib.auth import get_user_model
from apps.authentication.models import UserProfile
User = get_user_model()
if not User.objects.filter(email='admin@coworking.com').exists():
    user = User.objects.create_superuser('admin@coworking.com', 'admin@coworking.com', 'admin123')
    UserProfile.objects.create(user=user, full_name='Admin User', user_type_code='PartnerAdmin')
    print('Superuser created: admin@coworking.com / admin123')
"

echo "Platform ready at http://localhost:8000"
echo "Admin panel at http://localhost:8000/admin"
echo "API docs at http://localhost:8000/api/v1/"