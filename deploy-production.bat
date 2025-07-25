@echo off
echo 🚀 PRODUCTION DEPLOYMENT - BATTLE-READY COWORKING PLATFORM

echo ⚠️  CRITICAL: Ensure .env.production is configured with secure values!
pause

echo 🔧 Building production containers...
docker-compose -f docker-compose.prod.yml build --no-cache

echo 🗄️  Setting up production database...
docker-compose -f docker-compose.prod.yml up -d db redis
timeout /t 30 /nobreak

echo 🔄 Running production migrations...
docker-compose -f docker-compose.prod.yml run --rm web python manage.py migrate

echo 👤 Creating production superuser...
docker-compose -f docker-compose.prod.yml run --rm web python manage.py shell -c "
from django.contrib.auth import get_user_model
from apps.authentication.models import UserProfile
import os
User = get_user_model()
email = input('Admin email: ')
password = input('Admin password: ')
user = User.objects.create_superuser(email.split('@')[0], email, password)
UserProfile.objects.create(user=user, full_name='Production Admin', user_type_code='PartnerAdmin')
print(f'Production admin created: {email}')
"

echo 🚀 Starting production services...
docker-compose -f docker-compose.prod.yml up -d

echo ✅ Production deployment complete!
echo 🌐 Access: https://your-domain.com
echo 📊 Health: https://your-domain.com/health/
echo 🔧 Admin: https://your-domain.com/admin/

echo 🔍 Checking service status...
docker-compose -f docker-compose.prod.yml ps

pause