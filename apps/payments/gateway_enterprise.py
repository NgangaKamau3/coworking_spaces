import requests
import json
import logging
import time
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from .models import Payment

logger = logging.getLogger(__name__)

class PaymentGatewayError(Exception):
    """Custom exception for payment gateway errors"""
    pass

class EnterprisePaymentProcessor:
    """Enterprise-grade payment processor for Java Spring integration"""
    
    def __init__(self):
        self.gateway_url = settings.PAYMENT_GATEWAY_URL
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 1
    
    def process_payment(self, payment):
        """Process payment with retry logic and comprehensive error handling"""
        payload = {
            'amount': str(payment.amount),  # Use string for precision
            'currency': payment.currency,
            'payment_method': payment.payment_method_code,
            'reference': str(payment.payment_id),
            'customer_id': str(payment.booking.user.id),
            'description': f'Booking payment for {payment.booking.space.name}',
            'idempotency_key': getattr(payment, 'idempotency_key', str(payment.payment_id)),
            'timestamp': timezone.now().isoformat()
        }
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Payment attempt {attempt + 1} for {payment.payment_id}")
                
                response = requests.post(
                    f'{self.gateway_url}/api/payments/process',
                    json=payload,
                    timeout=self.timeout,
                    headers={
                        'Content-Type': 'application/json',
                        'X-API-Key': getattr(settings, 'PAYMENT_GATEWAY_API_KEY', 'demo-key'),
                        'X-Idempotency-Key': payload['idempotency_key']
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Payment {payment.payment_id} processed successfully")
                    return {
                        'success': True,
                        'transaction_id': result.get('transaction_id'),
                        'status': 'Paid',
                        'message': result.get('message', 'Payment successful'),
                        'gateway_response': result
                    }
                elif response.status_code == 400:
                    # Client error - don't retry
                    error_data = response.json()
                    logger.error(f"Payment {payment.payment_id} failed: {error_data}")
                    return {
                        'success': False,
                        'status': 'Failed',
                        'error': error_data.get('message', 'Payment validation failed'),
                        'gateway_response': error_data
                    }
                elif response.status_code >= 500:
                    # Server error - retry
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Gateway server error, retrying in {self.retry_delay}s")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        raise PaymentGatewayError(f"Gateway server error: {response.status_code}")
                else:
                    raise PaymentGatewayError(f"Unexpected response: {response.status_code}")
                    
            except requests.Timeout:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Payment timeout, retrying in {self.retry_delay}s")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    raise PaymentGatewayError("Payment gateway timeout")
                    
            except requests.ConnectionError:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Connection error, retrying in {self.retry_delay}s")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    raise PaymentGatewayError("Cannot connect to payment gateway")
                    
            except Exception as e:
                logger.error(f"Unexpected error processing payment: {str(e)}")
                raise PaymentGatewayError(f"Payment processing error: {str(e)}")
        
        # If we get here, all retries failed
        raise PaymentGatewayError("Payment processing failed after all retries")