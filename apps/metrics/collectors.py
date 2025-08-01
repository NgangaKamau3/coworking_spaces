"""Custom business metrics collection for enterprise monitoring"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps

# Business Metrics
payment_counter = Counter(
    'payments_total', 
    'Total payments processed',
    ['method', 'status', 'currency']
)

booking_counter = Counter(
    'bookings_total',
    'Total bookings created',
    ['venue_type', 'status']
)

booking_duration = Histogram(
    'booking_duration_seconds',
    'Booking processing time',
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

payment_amount = Histogram(
    'payment_amount',
    'Payment amounts processed',
    ['currency'],
    buckets=[10, 50, 100, 500, 1000, 5000]
)

active_users = Gauge(
    'active_users_current',
    'Currently active users'
)

venue_occupancy = Gauge(
    'venue_occupancy_rate',
    'Current venue occupancy rate',
    ['venue_id', 'venue_type']
)

api_requests = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

response_time = Histogram(
    'api_response_time_seconds',
    'API response time',
    ['method', 'endpoint']
)

# Application Info
app_info = Info('coworking_platform_info', 'Application information')
app_info.info({
    'version': '1.0.0',
    'environment': 'production'
})

def track_payment(method: str, status: str, currency: str, amount: float):
    """Track payment metrics"""
    payment_counter.labels(method=method, status=status, currency=currency).inc()
    payment_amount.labels(currency=currency).observe(amount)

def track_booking(venue_type: str, status: str, duration: float):
    """Track booking metrics"""
    booking_counter.labels(venue_type=venue_type, status=status).inc()
    booking_duration.observe(duration)

def track_api_request(method: str, endpoint: str, status: int, duration: float):
    """Track API request metrics"""
    api_requests.labels(method=method, endpoint=endpoint, status=status).inc()
    response_time.labels(method=method, endpoint=endpoint).observe(duration)

def metrics_middleware(get_response):
    """Django middleware to track API metrics"""
    def middleware(request):
        start_time = time.time()
        response = get_response(request)
        duration = time.time() - start_time
        
        track_api_request(
            method=request.method,
            endpoint=request.path,
            status=response.status_code,
            duration=duration
        )
        return response
    return middleware

def track_execution_time(metric_name: str):
    """Decorator to track function execution time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            if metric_name == 'booking':
                booking_duration.observe(duration)
            
            return result
        return wrapper
    return decorator