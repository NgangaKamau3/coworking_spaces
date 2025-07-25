from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
import re

class SecurityMiddleware(MiddlewareMixin):
    """Security middleware for additional protection"""
    
    SUSPICIOUS_PATTERNS = [
        r'<script.*?>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'union.*select',
        r'drop.*table',
    ]
    
    def process_request(self, request):
        # Basic XSS protection
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, str(request.body), re.IGNORECASE):
                return HttpResponseForbidden("Suspicious content detected")
        
        # Rate limiting headers
        request.META['HTTP_X_REAL_IP'] = self.get_client_ip(request)
        return None
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip