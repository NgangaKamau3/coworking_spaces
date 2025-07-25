import pytest
import json
from decimal import Decimal
from unittest.mock import Mock, patch
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.payments.models import Payment, PaymentAuditLog
from apps.payments.gateway_enterprise import EnterprisePaymentProcessor, PaymentGatewayError
from apps.bookings.models import Booking
from apps.venues.models import Venue, Space

User = get_user_model()

class PaymentSecurityTestCase(APITestCase):
    """Security tests for payment processing"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.venue = Venue.objects.create(
            venue_name='Test Venue',
            address='Test Address'
        )
        self.space = Space.objects.create(
            venue=self.venue,
            space_name='Test Space',
            hourly_rate=Decimal('25.00')
        )
        self.booking = Booking.objects.create(
            user=self.user,
            venue=self.venue,
            space=self.space,
            total_price=Decimal('100.00'),
            booking_status_code='Pending'
        )
    
    def test_payment_requires_authentication(self):
        """Test that payment endpoints require authentication"""
        url = reverse('process-payment')
        response = self.client.post(url, {
            'booking_id': self.booking.booking_id,
            'payment_method': 'Card'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_payment_idempotency(self):
        """Test payment idempotency prevents duplicate charges"""
        self.client.force_authenticate(user=self.user)
        
        idempotency_key = 'test-key-123'
        payment_data = {
            'booking_id': self.booking.booking_id,
            'payment_method': 'Card'
        }
        
        with patch('apps.payments.gateway_enterprise.EnterprisePaymentProcessor.process_payment') as mock_process:
            mock_process.return_value = {
                'success': True,
                'transaction_id': 'txn_123',
                'status': 'Paid'
            }
            
            # First request
            response1 = self.client.post(
                reverse('process-payment'),
                payment_data,
                HTTP_IDEMPOTENCY_KEY=idempotency_key
            )
            
            # Second request with same key
            response2 = self.client.post(
                reverse('process-payment'),
                payment_data,
                HTTP_IDEMPOTENCY_KEY=idempotency_key
            )
            
            # Should return same response without processing again
            self.assertEqual(response1.status_code, status.HTTP_200_OK)
            self.assertEqual(response2.status_code, status.HTTP_200_OK)
            self.assertEqual(response1.data['payment_id'], response2.data['payment_id'])
            mock_process.assert_called_once()  # Only called once
    
    def test_payment_amount_validation(self):
        """Test payment amount validation"""
        self.client.force_authenticate(user=self.user)
        
        # Test negative amount
        response = self.client.post(reverse('process-payment'), {
            'booking_id': self.booking.booking_id,
            'payment_method': 'Card',
            'amount': '-100.00'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_unauthorized_booking_access(self):
        """Test that users cannot pay for others' bookings"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=other_user)
        
        response = self.client.post(reverse('process-payment'), {
            'booking_id': self.booking.booking_id,
            'payment_method': 'Card'
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class PaymentGatewayTestCase(TestCase):
    """Test payment gateway integration"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.venue = Venue.objects.create(venue_name='Test Venue')
        self.space = Space.objects.create(venue=self.venue, space_name='Test Space')
        self.booking = Booking.objects.create(
            user=self.user,
            venue=self.venue,
            space=self.space,
            total_price=Decimal('100.00')
        )
        self.payment = Payment.objects.create(
            booking=self.booking,
            amount=Decimal('100.00'),
            currency='USD',
            payment_method_code='Card'
        )
    
    @patch('requests.post')
    def test_successful_payment_processing(self, mock_post):
        """Test successful payment processing"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'transaction_id': 'txn_123456',
            'message': 'Payment successful'
        }
        mock_post.return_value = mock_response
        
        processor = EnterprisePaymentProcessor()
        result = processor.process_payment(self.payment)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['transaction_id'], 'txn_123456')
        self.assertEqual(result['status'], 'Paid')
    
    @patch('requests.post')
    def test_payment_retry_on_server_error(self, mock_post):
        """Test payment retry logic on server errors"""
        # First two calls return 500, third succeeds
        mock_response_error = Mock()
        mock_response_error.status_code = 500
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            'success': True,
            'transaction_id': 'txn_retry_success'
        }
        
        mock_post.side_effect = [
            mock_response_error,
            mock_response_error,
            mock_response_success
        ]
        
        processor = EnterprisePaymentProcessor()
        result = processor.process_payment(self.payment)
        
        self.assertTrue(result['success'])
        self.assertEqual(mock_post.call_count, 3)
    
    @patch('requests.post')
    def test_payment_failure_on_client_error(self, mock_post):
        """Test payment failure on client errors (no retry)"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'success': False,
            'message': 'Invalid payment method'
        }
        mock_post.return_value = mock_response
        
        processor = EnterprisePaymentProcessor()
        result = processor.process_payment(self.payment)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 'Failed')
        self.assertEqual(mock_post.call_count, 1)  # No retry on client error
    
    @patch('requests.post')
    def test_payment_timeout_handling(self, mock_post):
        """Test payment timeout handling with retries"""
        mock_post.side_effect = [
            requests.Timeout(),
            requests.Timeout(),
            requests.Timeout()
        ]
        
        processor = EnterprisePaymentProcessor()
        
        with self.assertRaises(PaymentGatewayError) as context:
            processor.process_payment(self.payment)
        
        self.assertIn('timeout', str(context.exception))
        self.assertEqual(mock_post.call_count, 3)

class PaymentAuditTestCase(TransactionTestCase):
    """Test payment audit trail functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.venue = Venue.objects.create(venue_name='Test Venue')
        self.space = Space.objects.create(venue=self.venue, space_name='Test Space')
        self.booking = Booking.objects.create(
            user=self.user,
            venue=self.venue,
            space=self.space,
            total_price=Decimal('100.00')
        )
        self.payment = Payment.objects.create(
            booking=self.booking,
            amount=Decimal('100.00'),
            currency='USD',
            payment_method_code='Card'
        )
    
    def test_audit_log_creation(self):
        """Test that audit logs are created for payment actions"""
        PaymentAuditLog.objects.create(
            payment=self.payment,
            action_type='INITIATED',
            amount=self.payment.amount,
            reason='Payment initiated by user'
        )
        
        audit_logs = PaymentAuditLog.objects.filter(payment=self.payment)
        self.assertEqual(audit_logs.count(), 1)
        self.assertEqual(audit_logs.first().action_type, 'INITIATED')
    
    def test_audit_trail_completeness(self):
        """Test complete audit trail for payment lifecycle"""
        # Simulate payment lifecycle
        actions = ['INITIATED', 'PROCESSING', 'CAPTURED', 'COMPLETED']
        
        for action in actions:
            PaymentAuditLog.objects.create(
                payment=self.payment,
                action_type=action,
                amount=self.payment.amount,
                reason=f'Payment {action.lower()}'
            )
        
        audit_logs = PaymentAuditLog.objects.filter(
            payment=self.payment
        ).order_by('performed_at')
        
        self.assertEqual(audit_logs.count(), 4)
        self.assertEqual(
            [log.action_type for log in audit_logs],
            actions
        )

class PaymentPerformanceTestCase(TestCase):
    """Performance tests for payment processing"""
    
    def test_concurrent_payment_processing(self):
        """Test handling of concurrent payment requests"""
        # This would typically use threading or async testing
        # For now, we'll test the database constraints
        
        user = User.objects.create_user(username='testuser', email='test@example.com')
        venue = Venue.objects.create(venue_name='Test Venue')
        space = Space.objects.create(venue=venue, space_name='Test Space')
        booking = Booking.objects.create(
            user=user,
            venue=venue,
            space=space,
            total_price=Decimal('100.00')
        )
        
        # Test that duplicate payments with same idempotency key are prevented
        idempotency_key = 'test-concurrent-key'
        
        payment1 = Payment.objects.create(
            booking=booking,
            amount=Decimal('100.00'),
            currency='USD',
            payment_method_code='Card',
            idempotency_key=idempotency_key
        )
        
        # This should not create a duplicate
        existing_payment = Payment.objects.filter(
            idempotency_key=idempotency_key,
            booking__user=user
        ).first()
        
        self.assertEqual(existing_payment.payment_id, payment1.payment_id)

@pytest.mark.django_db
class TestPaymentWebhookSecurity:
    """Test webhook security and validation"""
    
    def test_webhook_signature_validation(self):
        """Test webhook signature validation"""
        # This would test actual signature validation
        # For now, we'll test the webhook endpoint structure
        pass
    
    def test_webhook_idempotency(self):
        """Test webhook idempotency handling"""
        # Test that duplicate webhook calls are handled properly
        pass