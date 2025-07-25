import pytest
from django.conf import settings
from django.test.utils import get_runner

def pytest_configure():
    import django
    settings.configure(
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.contrib.gis.db.backends.spatialite',
                'NAME': ':memory:'
            }
        },
        SITE_ID=1,
        SECRET_KEY='test-secret-key',
        USE_I18N=True,
        USE_L10N=True,
        STATIC_URL='/static/',
        ROOT_URLCONF='config.urls',
        TEMPLATES=[
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'APP_DIRS': True,
                'OPTIONS': {
                    "context_processors": [
                        "django.template.context_processors.request",
                        "django.contrib.auth.context_processors.auth",
                        "django.contrib.messages.context_processors.messages",
                    ],
                },
            },
        ],
        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ],
        INSTALLED_APPS=[
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'django.contrib.gis',
            'rest_framework',
            'apps.authentication',
            'apps.venues',
            'apps.bookings',
            'apps.payments',
            'apps.billing',
            'apps.iot',
            'apps.reviews',
            'apps.audit',
        ],
        PASSWORD_HASHERS=[
            'django.contrib.auth.hashers.MD5PasswordHasher',
        ],
        ENCRYPTION_KEY='test-encryption-key-32-characters',
        IOT_WEBHOOK_SECRET='test-iot-secret',
    )

    django.setup()

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def user_factory():
    from django.contrib.auth import get_user_model
    from apps.authentication.models import UserProfile
    
    User = get_user_model()
    
    def create_user(email='test@example.com', user_type='Individual', **kwargs):
        user = User.objects.create_user(
            username=email,
            email=email,
            password='testpass123',
            **kwargs
        )
        UserProfile.objects.create(
            user=user,
            full_name=kwargs.get('full_name', 'Test User'),
            user_type_code=user_type
        )
        return user
    
    return create_user

@pytest.fixture
def venue_factory():
    from django.contrib.gis.geos import Point
    from apps.venues.models import Venue
    
    def create_venue(owner_user=None, **kwargs):
        defaults = {
            'venue_name': 'Test Venue',
            'venue_type_code': 'CoworkingHub',
            'address': '123 Test St',
            'city': 'Test City',
            'country_code': 'US',
            'location': Point(-74.0060, 40.7128),
            'operating_hours_json': {'monday': '9:00-18:00'},
            'pricing_model': 'hourly',
            'owner_user': owner_user
        }
        defaults.update(kwargs)
        return Venue.objects.create(**defaults)
    
    return create_venue

@pytest.fixture
def space_factory():
    from apps.venues.models import Space
    
    def create_space(venue, **kwargs):
        defaults = {
            'space_name': 'Test Space',
            'capacity': 4,
            'hourly_rate': 20.00,
            'space_type_code': 'Boardroom'
        }
        defaults.update(kwargs)
        return Space.objects.create(venue=venue, **defaults)
    
    return create_space

@pytest.fixture
def booking_factory():
    from django.utils import timezone
    from apps.bookings.models import Booking
    
    def create_booking(user, venue, space=None, **kwargs):
        start_time = timezone.now() + timezone.timedelta(hours=1)
        end_time = start_time + timezone.timedelta(hours=2)
        
        defaults = {
            'booking_start_time': start_time,
            'booking_end_time': end_time,
            'booking_status_code': 'Pending',
            'payment_status_code': 'Pending',
            'total_price': 40.00
        }
        defaults.update(kwargs)
        
        return Booking.objects.create(
            user=user,
            venue=venue,
            space=space,
            **defaults
        )
    
    return create_booking