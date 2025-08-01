import json
from uuid import uuid4
from django.utils.deprecation import MiddlewareMixin
from apps.audit.models import UserActivityLog

class AuditMiddleware(MiddlewareMixin):
    """Middleware for audit trail logging"""
    
    def process_request(self, request):
        request.audit_id = str(uuid4())
        return None
    
    def process_response(self, request, response):
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                UserActivityLog.objects.create(
                    user_id=request.user.id,
                    activity_type=f"{request.method} {request.path}",
                    activity_desc=f"API call to {request.path}",
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                )
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip