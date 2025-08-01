"""Domain-specific exceptions for enterprise error handling"""

class DomainException(Exception):
    """Base domain exception"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(message)

class PaymentFailed(DomainException):
    """Payment processing failed"""
    def __init__(self, reason: str, transaction_id: str = None, amount: float = None):
        self.reason = reason
        self.transaction_id = transaction_id
        self.amount = amount
        super().__init__(f"Payment failed: {reason}", "PAYMENT_FAILED")

class VenueUnavailable(DomainException):
    """Venue is not available for booking"""
    def __init__(self, venue_id: str, requested_time):
        self.venue_id = venue_id
        self.requested_time = requested_time
        super().__init__(f"Venue {venue_id} unavailable at {requested_time}", "VENUE_UNAVAILABLE")

class BookingConflict(DomainException):
    """Booking time conflict detected"""
    def __init__(self, space_id: str, conflicting_time):
        self.space_id = space_id
        self.conflicting_time = conflicting_time
        super().__init__(f"Booking conflict for space {space_id}", "BOOKING_CONFLICT")

class InsufficientPermissions(DomainException):
    """User lacks required permissions"""
    def __init__(self, user_id: str, required_permission: str):
        self.user_id = user_id
        self.required_permission = required_permission
        super().__init__(f"User {user_id} lacks permission: {required_permission}", "INSUFFICIENT_PERMISSIONS")

class ServiceUnavailableError(DomainException):
    """External service is unavailable"""
    def __init__(self, service_name: str, retry_after: int = None):
        self.service_name = service_name
        self.retry_after = retry_after
        super().__init__(f"Service {service_name} unavailable", "SERVICE_UNAVAILABLE")