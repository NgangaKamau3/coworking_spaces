from django.contrib import admin
from django.urls import path, include
from apps.health import health_check
from apps.api_root import api_root

urlpatterns = [
    path('', health_check, name='health'),
    path('health/', health_check, name='health_check'),
    path('api/v1/', api_root, name='api_root'),
    path('admin/', admin.site.urls),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/venues/', include('apps.venues.urls')),
    path('api/v1/bookings/', include('apps.bookings.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
    path('api/v1/billing/', include('apps.billing.urls')),
    path('api/v1/iot/', include('apps.iot.urls')),
    path('api/v1/reviews/', include('apps.reviews.urls')),
]