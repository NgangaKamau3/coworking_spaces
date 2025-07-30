import os
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.authentication.models import UserProfile, Company
from apps.authentication.serializers import UserRegistrationSerializer

User = get_user_model()

class AuthenticationTestCase(TestCase):
    """Test authentication functionality"""
    
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'email': 'test@example.com',
            'password': os.getenv('TEST_USER_PASSWORD', 'secure_test_pass_123'),
            'full_name': 'Test User',
            'user_type_code': 'Individual',
            'phone_number': '+1234567890'
        }
    
    def test_user_registration_success(self):
        """Test successful user registration"""
        response = self.client.post('/api/v1/auth/register/', self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user created
        user = User.objects.get(email=self.user_data['email'])
        self.assertTrue(user.check_password(self.user_data['password']))
        
        # Verify profile created
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.full_name, self.user_data['full_name'])
        self.assertEqual(profile.user_type_code, self.user_data['user_type_code'])
    
    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email"""
        # Create first user
        self.client.post('/api/v1/auth/register/', self.user_data)
        
        # Try to create second user with same email
        response = self.client.post('/api/v1/auth/register/', self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_oauth_token_success(self):
        """Test OAuth token generation"""
        # Create user first
        self.client.post('/api/v1/auth/register/', self.user_data)
        
        # Request token
        token_data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        response = self.client.post('/api/v1/auth/token/', token_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
    
    def test_oauth_token_invalid_credentials(self):
        """Test OAuth token with invalid credentials"""
        token_data = {
            'email': 'invalid@example.com',
            'password': 'wrongpass'
        }
        response = self.client.post('/api/v1/auth/token/', token_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_profile_update(self):
        """Test user profile update"""
        # Create and authenticate user
        user = User.objects.create_user(
            username=self.user_data['email'],
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        UserProfile.objects.create(
            user=user,
            full_name=self.user_data['full_name'],
            user_type_code=self.user_data['user_type_code']
        )
        
        self.client.force_authenticate(user=user)
        
        # Update profile
        update_data = {'full_name': 'Updated Name'}
        response = self.client.patch('/api/v1/auth/profile/', update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify update
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.full_name, 'Updated Name')

class CompanyTestCase(TestCase):
    """Test company management"""
    
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin@company.com',
            email='admin@company.com',
            password=os.getenv('TEST_ADMIN_PASSWORD', 'secure_admin_pass_123')
        )
        UserProfile.objects.create(
            user=self.admin_user,
            full_name='Admin User',
            user_type_code='CorporateAdmin'
        )
        self.client.force_authenticate(user=self.admin_user)
    
    def test_company_creation(self):
        """Test company creation by corporate admin"""
        company_data = {
            'company_name': 'Test Company',
            'subscription_plan_code': 'Premium',
            'billing_cycle_code': 'Monthly'
        }
        response = self.client.post('/api/v1/auth/companies/', company_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify company created
        company = Company.objects.get(company_name='Test Company')
        self.assertEqual(company.created_by_user, self.admin_user)
    
    def test_company_list(self):
        """Test company listing"""
        Company.objects.create(
            company_name='Test Company',
            created_by_user=self.admin_user
        )
        
        response = self.client.get('/api/v1/auth/companies/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)