import uuid
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from apps.authentication.models import User

class UserActivityLog(models.Model):
    """Comprehensive user activity logging"""
    
    ACTIVITY_TYPES = [
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('CREATE', 'Create Operation'),
        ('UPDATE', 'Update Operation'),
        ('DELETE', 'Delete Operation'),
        ('VIEW', 'View Operation'),
        ('PAYMENT', 'Payment Operation'),
        ('BOOKING', 'Booking Operation'),
    ]
    
    activity_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    activity_desc = models.TextField()
    
    # Generic foreign key for related entities
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    
    # Request details
    request_method = models.CharField(max_length=10, blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_data = models.JSONField(default=dict, blank=True)
    response_status = models.IntegerField(null=True, blank=True)
    
    activity_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activity_log'
        indexes = [
            models.Index(fields=['user', 'activity_time']),
            models.Index(fields=['activity_type', 'activity_time']),
            models.Index(fields=['ip_address']),
        ]
        ordering = ['-activity_time']

class DataAccessLog(models.Model):
    """GDPR compliance - data access logging"""
    
    ACCESS_TYPES = [
        ('READ', 'Data Read'),
        ('EXPORT', 'Data Export'),
        ('DELETE', 'Data Deletion'),
        ('ANONYMIZE', 'Data Anonymization'),
    ]
    
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    accessed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='data_access_logs')
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPES)
    data_fields = models.JSONField(default=list)  # List of accessed fields
    reason = models.TextField()
    legal_basis = models.CharField(max_length=100)  # GDPR legal basis
    accessed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['accessed_user', 'accessed_at']),
            models.Index(fields=['access_type']),
        ]

class SystemAuditLog(models.Model):
    """System-level audit logging"""
    
    SEVERITY_LEVELS = [
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    component = models.CharField(max_length=100)  # System component
    event_type = models.CharField(max_length=50)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    message = models.TextField()
    details = models.JSONField(default=dict)
    
    # Optional user context
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['component', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
        ]
        ordering = ['-timestamp']

class SecurityEvent(models.Model):
    """Security-related events logging"""
    
    EVENT_TYPES = [
        ('FAILED_LOGIN', 'Failed Login Attempt'),
        ('SUSPICIOUS_ACTIVITY', 'Suspicious Activity'),
        ('UNAUTHORIZED_ACCESS', 'Unauthorized Access Attempt'),
        ('RATE_LIMIT_EXCEEDED', 'Rate Limit Exceeded'),
        ('INVALID_TOKEN', 'Invalid Token Usage'),
        ('PRIVILEGE_ESCALATION', 'Privilege Escalation Attempt'),
    ]
    
    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    description = models.TextField()
    
    # User context (may be null for anonymous attempts)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    username_attempted = models.CharField(max_length=150, blank=True)
    
    # Network context
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Request context
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    
    # Additional details
    metadata = models.JSONField(default=dict)
    risk_score = models.IntegerField(default=0)  # 0-100 risk assessment
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['risk_score']),
        ]
        ordering = ['-timestamp']

class ComplianceLog(models.Model):
    """Compliance and regulatory logging"""
    
    COMPLIANCE_TYPES = [
        ('GDPR_REQUEST', 'GDPR Data Request'),
        ('DATA_RETENTION', 'Data Retention Policy'),
        ('CONSENT_CHANGE', 'Consent Status Change'),
        ('DATA_BREACH', 'Data Breach Incident'),
        ('AUDIT_TRAIL', 'Audit Trail Access'),
    ]
    
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    compliance_type = models.CharField(max_length=20, choices=COMPLIANCE_TYPES)
    subject_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compliance_logs')
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    description = models.TextField()
    actions_taken = models.JSONField(default=list)
    evidence = models.JSONField(default=dict)
    
    # Compliance metadata
    regulation = models.CharField(max_length=50, default='GDPR')
    retention_period = models.IntegerField(null=True, blank=True)  # Days
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['compliance_type', 'timestamp']),
            models.Index(fields=['subject_user', 'timestamp']),
        ]
        ordering = ['-timestamp']