import uuid
from django.db import models
from apps.bookings.models import Booking
from apps.authentication.models import User
from core.utils.encryption import encryption

class Payment(models.Model):
    """Payment model with audit trail"""
    
    PAYMENT_METHODS = [
        ('Card', 'Credit/Debit Card'),
        ('Mpesa', 'Mobile Money'),
        ('PayPal', 'PayPal'),
        ('Wallet', 'Internal Wallet'),
    ]
    
    PAYMENT_STATUS = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]
    
    payment_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_method_code = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_ref = models.CharField(max_length=255, blank=True)
    payment_timestamp = models.DateTimeField(auto_now_add=True)
    status_code = models.CharField(max_length=20, choices=PAYMENT_STATUS)
    gateway_payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Encrypted sensitive data
    _encrypted_card_last4 = models.TextField(blank=True)
    
    class Meta:
        db_table = 'payment'
        indexes = [
            models.Index(fields=['booking']),
            models.Index(fields=['status_code']),
        ]
    
    @property
    def card_last4(self):
        return encryption.decrypt(self._encrypted_card_last4) if self._encrypted_card_last4 else ''
    
    @card_last4.setter
    def card_last4(self, value):
        self._encrypted_card_last4 = encryption.encrypt(value) if value else ''

class PaymentAuditLog(models.Model):
    """Payment audit trail"""
    
    ACTION_TYPES = [
        ('CAPTURED', 'Payment Captured'),
        ('REFUNDED', 'Payment Refunded'),
        ('FAILED', 'Payment Failed'),
        ('CANCELLED', 'Payment Cancelled'),
    ]
    
    audit_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='audit_logs')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    performed_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField(blank=True)
    performed_at = models.DateTimeField(auto_now_add=True)
    snapshot_json = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'payment_audit_log'

class PaymentGatewayConfig(models.Model):
    """Payment gateway configuration"""
    
    GATEWAY_TYPES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('mpesa', 'M-Pesa'),
        ('java_spring', 'Java Spring Service'),
    ]
    
    config_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    gateway_type = models.CharField(max_length=20, choices=GATEWAY_TYPES)
    gateway_name = models.CharField(max_length=100)
    endpoint_url = models.URLField()
    is_active = models.BooleanField(default=True)
    config_json = models.JSONField(default=dict)  # Gateway-specific configuration
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Encrypted credentials
    _encrypted_api_key = models.TextField(blank=True)
    _encrypted_secret_key = models.TextField(blank=True)
    
    @property
    def api_key(self):
        return encryption.decrypt(self._encrypted_api_key) if self._encrypted_api_key else ''
    
    @api_key.setter
    def api_key(self, value):
        self._encrypted_api_key = encryption.encrypt(value) if value else ''
    
    @property
    def secret_key(self):
        return encryption.decrypt(self._encrypted_secret_key) if self._encrypted_secret_key else ''
    
    @secret_key.setter
    def secret_key(self, value):
        self._encrypted_secret_key = encryption.encrypt(value) if value else ''