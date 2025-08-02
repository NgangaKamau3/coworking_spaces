"""High-grade test configuration for enterprise testing"""

import os
import pytest
from django.test import override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from unittest.mock import Mock

User = get_user_model()

@pytest.fixture
def api_client():
    """API client for testing"""
    return APIClient()

@pytest.fixture
def test_user():
    """Create test user"""
    return User.objects.create_user(
        username='testuser@example.com',
        email='testuser@example.com',
        password=os.getenv('TEST_USER_PASSWORD', 'secure_test_pass_123')
    )

@pytest.fixture
def admin_user():
    """Create admin user"""
    return User.objects.create_user(
        username='admin@example.com',
        email='admin@example.com',
        password=os.getenv('TEST_ADMIN_PASSWORD', 'secure_admin_pass_123'),
        is_staff=True
    )

@pytest.fixture
def mock_venue():
    """Mock venue for testing"""
    venue = Mock()
    venue.venue_id = 'test-venue-123'
    venue.venue_name = 'Test Venue'
    return venue

@pytest.fixture
def mock_space():
    """Mock space for testing"""
    space = Mock()
    space.space_id = 'test-space-123'
    space.space_name = 'Test Space'
    space.hourly_rate = 20.00
    return space

@pytest.fixture
def authenticated_client(api_client, test_user):
    """API client with authenticated user"""
    api_client.force_authenticate(user=test_user)
    return api_client

@pytest.fixture
def admin_client(api_client, admin_user):
    """API client with admin user"""
    api_client.force_authenticate(user=admin_user)
    return api_client

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests"""
    pass

@pytest.fixture
def mock_payment_gateway():
    """Mock payment gateway for testing"""
    from unittest.mock import Mock
    gateway = Mock()
    gateway.process_payment.return_value = {
        'success': True,
        'transaction_id': 'test_txn_123',
        'status': 'Paid'
    }
    return gateway