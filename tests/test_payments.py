import os
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from apps.authentication.models import UserProfile
from apps.venues.models import Venue, Space
from apps.bookings.models import Booking
from apps.payments.models import Payment, PaymentAuditLog
from apps.payments.gateway import PaymentProcessor

User = get_user_model()

class PaymentTestCase(TestCase):
    """Test payment processing"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create user
        self.user = User.objects.create_user(
            username='user@example.com',
            email='user@example.com',
            password=os.getenv('TEST_USER_PASSWORD', 'secure_test_pass_123')
        )
        UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            user_type_code='Individual'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create venue, space, and booking
        self.venue = Venue.objects.create(
            venue_name='Test Venue',
            venue_type_code='CoworkingHub',
            address='123 Test St',
            city='Test City',
            country_code='US',
            location=Point(-74.0060, 40.7128),
            operating_hours_json={'monday': '9:00-18:00'},
            pricing_model='hourly'
        )
        
        self.space = Space.objects.create(
            venue=self.venue,
            space_name='Meeting Room',
            capacity=6,
            hourly_rate=20.00,
            space_type_code='Boardroom'
        )
        
        start_time = timezone.now() + timezone.timedelta(hours=1)
        end_time = start_time + timezone.timedelta(hours=2)
        
        self.booking = Booking.objects.create(
            user=self.user,
            venue=self.venue,
            space=self.space,
            booking_start_time=start_time,
            booking_end_time=end_time,
            booking_status_code='Pending',
            payment_status_code='Pending',
            total_price=40.00
        )
    
    @patch('apps.payments.gateway.JavaSpringPaymentGateway.process_payment')
    def test_payment_processing_success(self, mock_process_payment):
        """Test successful payment processing"""
        # Mock successful payment response
        mock_process_payment.return_value = {
            'success': True,
            'transaction_id': 'txn_123456',
            'status': 'completed'
        }
        
        payment_data = {
            'booking_id': str(self.booking.booking_id),
            'payment_method': 'Card'
        }
        
        response = self.client.post('/api/v1/payments/process/', payment_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        # Verify payment record created
        payment = Payment.objects.get(booking=self.booking)
        self.assertEqual(payment.status_code, 'Paid')
        self.assertEqual(payment.transaction_ref, 'txn_123456')
        
        # Verify booking payment status updated
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.payment_status_code, 'Paid')
        
        # Verify audit log created
        audit_log = PaymentAuditLog.objects.get(payment=payment)
        self.assertEqual(audit_log.action_type, 'CAPTURED')
    
    @patch('apps.payments.gateway.JavaSpringPaymentGateway.process_payment')
    def test_payment_processing_failure(self, mock_process_payment):
        """Test failed payment processing"""
        # Mock failed payment response
        mock_process_payment.return_value = {
            'success': False,
            'error': 'Insufficient funds'
        }
        
        payment_data = {
            'booking_id': str(self.booking.booking_id),
            'payment_method': 'Card'
        }
        
        response = self.client.post('/api/v1/payments/process/', payment_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'failed')
        
        # Verify payment record shows failure
        payment = Payment.objects.get(booking=self.booking)
        self.assertEqual(payment.status_code, 'Failed')
        
        # Verify audit log created
        audit_log = PaymentAuditLog.objects.get(payment=payment)
        self.assertEqual(audit_log.action_type, 'FAILED')
    
    @patch('apps.payments.gateway.JavaSpringPaymentGateway.refund_payment')
    def test_payment_refund_success(self, mock_refund_payment):
        """Test successful payment refund"""
        # Create paid payment
        payment = Payment.objects.create(
            booking=self.booking,
            amount=40.00,
            currency='USD',
            payment_method_code='Card',
            transaction_ref='txn_123456',
            status_code='Paid'
        )
        
        # Mock successful refund response
        mock_refund_payment.return_value = {
            'success': True,
            'refund_id': 'ref_123456'
        }
        
        refund_data = {
            'reason': 'Customer requested cancellation'
        }
        
        response = self.client.post(
            f'/api/v1/payments/{payment.payment_id}/refund/',
            refund_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify payment status updated
        payment.refresh_from_db()
        self.assertEqual(payment.status_code, 'Refunded')
        
        # Verify booking status updated
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.payment_status_code, 'Refunded')
        self.assertEqual(self.booking.booking_status_code, 'Cancelled')
        
        # Verify audit log created
        audit_log = PaymentAuditLog.objects.filter(
            payment=payment,
            action_type='REFUNDED'
        ).first()
        self.assertIsNotNone(audit_log)
    
    def test_payment_webhook_processing(self):
        """Test payment webhook processing"""
        # Create pending payment
        payment = Payment.objects.create(
            booking=self.booking,
            amount=40.00,
            currency='USD',
            payment_method_code='Card',
            transaction_ref='txn_123456',
            status_code='Pending'
        )
        
        webhook_data = {
            'transaction_id': 'txn_123456',
            'status': 'Paid',
            'amount': 40.00,
            'currency': 'USD'
        }
        
        response = self.client.post(
            '/api/v1/payments/webhook/',
            webhook_data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify payment status updated
        payment.refresh_from_db()
        self.assertEqual(payment.status_code, 'Paid')
        
        # Verify booking status updated
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.payment_status_code, 'Paid')
    
    def test_payment_list_for_user(self):
        """Test payment list retrieval for user"""
        # Create multiple payments
        Payment.objects.create(
            booking=self.booking,
            amount=40.00,
            currency='USD',
            payment_method_code='Card',
            status_code='Paid'
        )
        
        # Create another booking and payment
        start_time = timezone.now() + timezone.timedelta(hours=3)
        end_time = start_time + timezone.timedelta(hours=1)
        
        booking2 = Booking.objects.create(
            user=self.user,
            venue=self.venue,
            space=self.space,
            booking_start_time=start_time,
            booking_end_time=end_time,
            booking_status_code='Pending',
            payment_status_code='Failed',
            total_price=20.00
        )
        
        Payment.objects.create(
            booking=booking2,
            amount=20.00,
            currency='USD',
            payment_method_code='PayPal',
            status_code='Failed'
        )
        
        response = self.client.get('/api/v1/payments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_payment_audit_log_retrieval(self):
        """Test payment audit log retrieval"""
        payment = Payment.objects.create(
            booking=self.booking,
            amount=40.00,
            currency='USD',
            payment_method_code='Card',
            status_code='Paid'
        )
        
        # Create audit logs
        PaymentAuditLog.objects.create(
            payment=payment,
            action_type='CAPTURED',
            amount=40.00,
            snapshot_json={'status': 'success'}
        )
        
        PaymentAuditLog.objects.create(
            payment=payment,
            action_type='REFUNDED',
            amount=40.00,
            reason='Customer request',
            snapshot_json={'refund_id': 'ref_123'}
        )
        
        response = self.client.get(f'/api/v1/payments/{payment.payment_id}/audit/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

class PaymentSecurityTestCase(TestCase):
    """Test payment security features"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_payment_webhook_without_authentication(self):
        """Test webhook endpoint allows unauthenticated requests"""
        webhook_data = {
            'transaction_id': 'txn_123456',
            'status': 'Paid'
        }
        
        # Should not require authentication
        response = self.client.post(
            '/api/v1/payments/webhook/',
            webhook_data,
            content_type='application/json'
        )
        # Will return 404 for non-existent payment, but not 401 for auth
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_payment_data_encryption(self):
        """Test sensitive payment data encryption"""
        user = User.objects.create_user(
            username='user@example.com',
            email='user@example.com',
            password=os.getenv('TEST_USER_PASSWORD', 'secure_test_pass_123')
        )
        
        venue = Venue.objects.create(
            venue_name='Test Venue',
            venue_type_code='CoworkingHub',
            address='123 Test St',
            city='Test City',
            country_code='US',
            location=Point(-74.0060, 40.7128),
            operating_hours_json={'monday': '9:00-18:00'},
            pricing_model='hourly'
        )
        
        booking = Booking.objects.create(
            user=user,
            venue=venue,
            booking_start_time=timezone.now() + timezone.timedelta(hours=1),
            booking_end_time=timezone.now() + timezone.timedelta(hours=2),
            booking_status_code='Pending',
            payment_status_code='Pending',
            total_price=40.00
        )
        
        payment = Payment.objects.create(
            booking=booking,
            amount=40.00,
            currency='USD',
            payment_method_code='Card',
            status_code='Paid'
        )
        
        # Set encrypted card data
        payment.card_last4 = '1234'
        payment.save()
        
        # Verify data is encrypted in database
        payment.refresh_from_db()
        self.assertNotEqual(payment._encrypted_card_last4, '1234')
        self.assertEqual(payment.card_last4, '1234')