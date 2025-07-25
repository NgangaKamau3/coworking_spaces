import requests
import json
from abc import ABC, abstractmethod
from django.conf import settings
from .models import PaymentGatewayConfig, Payment, PaymentAuditLog

class PaymentGatewayInterface(ABC):
    """Abstract payment gateway interface"""
    
    @abstractmethod
    def process_payment(self, payment_data):
        pass
    
    @abstractmethod
    def refund_payment(self, payment_id, amount):
        pass
    
    @abstractmethod
    def get_payment_status(self, transaction_ref):
        pass

class JavaSpringPaymentGateway(PaymentGatewayInterface):
    """Java Spring payment service integration"""
    
    def __init__(self):
        self.config = PaymentGatewayConfig.objects.get(
            gateway_type='java_spring',
            is_active=True
        )
        self.base_url = self.config.endpoint_url
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.config.api_key}'
        }
    
    def process_payment(self, payment_data):
        """Process payment through Java Spring service"""
        endpoint = f"{self.base_url}/api/payments/process"
        
        payload = {
            'amount': float(payment_data['amount']),
            'currency': payment_data['currency'],
            'payment_method': payment_data['payment_method'],
            'booking_id': str(payment_data['booking_id']),
            'customer_id': str(payment_data['customer_id']),
            'metadata': payment_data.get('metadata', {})
        }
        
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    def refund_payment(self, payment_id, amount):
        """Refund payment through Java Spring service"""
        endpoint = f"{self.base_url}/api/payments/{payment_id}/refund"
        
        payload = {
            'amount': float(amount),
            'reason': 'Customer requested refund'
        }
        
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    def get_payment_status(self, transaction_ref):
        """Get payment status from Java Spring service"""
        endpoint = f"{self.base_url}/api/payments/{transaction_ref}/status"
        
        try:
            response = requests.get(
                endpoint,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {'success': False, 'error': str(e)}

class PaymentProcessor:
    """Main payment processor with gateway abstraction"""
    
    def __init__(self):
        self.gateways = {
            'java_spring': JavaSpringPaymentGateway(),
        }
    
    def process_payment(self, payment: Payment, gateway_type='java_spring'):
        """Process payment through specified gateway"""
        gateway = self.gateways.get(gateway_type)
        if not gateway:
            raise ValueError(f"Gateway {gateway_type} not supported")
        
        payment_data = {
            'amount': payment.amount,
            'currency': payment.currency,
            'payment_method': payment.payment_method_code,
            'booking_id': payment.booking.booking_id,
            'customer_id': payment.booking.user.id,
            'metadata': {
                'venue_name': payment.booking.venue.venue_name,
                'space_name': payment.booking.space.space_name if payment.booking.space else None,
            }
        }
        
        result = gateway.process_payment(payment_data)
        
        # Update payment status
        if result.get('success'):
            payment.status_code = 'Paid'
            payment.transaction_ref = result.get('transaction_id', '')
            payment.gateway_payload = result
            
            # Update booking payment status
            payment.booking.payment_status_code = 'Paid'
            payment.booking.save()
            
            # Create audit log
            PaymentAuditLog.objects.create(
                payment=payment,
                action_type='CAPTURED',
                amount=payment.amount,
                snapshot_json=result
            )
        else:
            payment.status_code = 'Failed'
            payment.gateway_payload = result
            
            PaymentAuditLog.objects.create(
                payment=payment,
                action_type='FAILED',
                amount=payment.amount,
                reason=result.get('error', 'Unknown error'),
                snapshot_json=result
            )
        
        payment.save()
        return result
    
    def refund_payment(self, payment: Payment, amount=None, reason=''):
        """Refund payment"""
        if payment.status_code != 'Paid':
            return {'success': False, 'error': 'Payment not in paid status'}
        
        refund_amount = amount or payment.amount
        gateway_type = 'java_spring'  # Default gateway
        gateway = self.gateways.get(gateway_type)
        
        result = gateway.refund_payment(payment.transaction_ref, refund_amount)
        
        if result.get('success'):
            payment.status_code = 'Refunded'
            payment.save()
            
            # Update booking status
            payment.booking.payment_status_code = 'Refunded'
            payment.booking.booking_status_code = 'Cancelled'
            payment.booking.save()
            
            # Create audit log
            PaymentAuditLog.objects.create(
                payment=payment,
                action_type='REFUNDED',
                amount=refund_amount,
                reason=reason,
                snapshot_json=result
            )
        
        return result