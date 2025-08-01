from uuid import uuid4
from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    is_deleted = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'auth_user_custom'

class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('Individual', 'Individual'),
        ('CorporateAdmin', 'Corporate Admin'),
        ('CorporateUser', 'Corporate User'),
        ('PartnerAdmin', 'Partner Admin'),
    ]
    
    ACCOUNT_STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Suspended', 'Suspended'),
        ('Deleted', 'Deleted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255)
    user_type_code = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    preferred_language = models.CharField(max_length=10, default='en')
    profile_picture_url = models.URLField(blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    account_status_code = models.CharField(max_length=20, choices=ACCOUNT_STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    phone_number = models.CharField(max_length=20, blank=True)
    
    class Meta:
        db_table = 'app_user'

class Company(models.Model):
    SUBSCRIPTION_PLANS = [
        ('Basic', 'Basic'),
        ('Premium', 'Premium'),
        ('Enterprise', 'Enterprise'),
    ]
    
    BILLING_CYCLES = [
        ('Monthly', 'Monthly'),
        ('Quarterly', 'Quarterly'),
        ('Annual', 'Annual'),
    ]
    
    company_id = models.UUIDField(primary_key=True, default=uuid4)
    company_name = models.CharField(max_length=255)
    subscription_plan_code = models.CharField(max_length=20, choices=SUBSCRIPTION_PLANS, blank=True)
    billing_cycle_code = models.CharField(max_length=20, choices=BILLING_CYCLES, blank=True)
    active_flag = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'company'