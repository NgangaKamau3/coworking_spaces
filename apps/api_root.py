import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """API root endpoint with available endpoints"""
    return Response({
        "message": "Coworking Platform API v1",
        "version": "1.0.0",
        "endpoints": {
            "authentication": "/api/v1/auth/",
            "venues": "/api/v1/venues/",
            "bookings": "/api/v1/bookings/",
            "payments": "/api/v1/payments/",
            "billing": "/api/v1/billing/",
            "iot": "/api/v1/iot/",
            "reviews": "/api/v1/reviews/",
            "health": "/health/"
        },
        "documentation": {k: v for k, v in {
            "admin": "/admin/" if os.getenv('DEBUG', 'False').lower() == 'true' else None,
            "oauth": "/o/"
        }.items() if v is not None}
    })