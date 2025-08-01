from dependency_injector import containers, providers
from apps.payments.gateway_enterprise import EnterprisePaymentProcessor
from apps.payments.services import PaymentService
from apps.bookings.services import BookingService
from apps.venues.services import VenueService

class Container(containers.DeclarativeContainer):
    """Enterprise dependency injection container"""
    
    config = providers.Configuration()
    
    # Payment Gateway
    payment_gateway = providers.Factory(
        EnterprisePaymentProcessor,
        gateway_url=config.payment.gateway_url,
        api_key=config.payment.api_key,
        timeout=config.payment.timeout.as_(int)
    )
    
    # Services
    payment_service = providers.Factory(
        PaymentService,
        gateway=payment_gateway
    )
    
    booking_service = providers.Factory(
        BookingService,
        payment_service=payment_service
    )
    
    venue_service = providers.Factory(
        VenueService
    )