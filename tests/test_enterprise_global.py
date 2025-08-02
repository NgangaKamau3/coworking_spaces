"""Global enterprise test suite with full dependencies"""

import pytest
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, Mock
import time
from decimal import Decimal
from django.utils import timezone

from apps.authentication.models import UserProfile, Company
from apps.venues.models import Venue, Space
from apps.bookings.models import Booking
from apps.payments.models import Payment
from apps.iot.models import Sensor, SensorReading

User = get_user_model()

@pytest.mark.unit
class GlobalUnitTests(TestCase):
    """Comprehensive unit tests with full model dependencies"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='global@example.com',
            email='global@example.com',
            password='secure_global_pass_123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            full_name='Global Test User',
            user_type_code='Individual'
        )
    
    def test_user_profile_creation(self):
        """Test user profile creation with all fields"""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.full_name, 'Global Test User')
        self.assertEqual(self.profile.user_type_code, 'Individual')
    
    def test_venue_creation_with_location(self):
        """Test venue creation with geospatial data"""
        venue = Venue.objects.create(
            venue_name='Global Test Venue',
            venue_type_code='CoworkingHub',
            address='123 Global St',
            city='Global City',
            country_code='US',
            location=Point(-74.0060, 40.7128),
            operating_hours_json={'monday': '9:00-18:00'},
            pricing_model='hourly',
            owner_user=self.user
        )
        
        self.assertEqual(venue.venue_name, 'Global Test Venue')
        self.assertIsNotNone(venue.location)
        self.assertEqual(venue.location.x, -74.0060)
        self.assertEqual(venue.location.y, 40.7128)

@pytest.mark.integration
class GlobalIntegrationTests(APITestCase):
    """Full integration tests with complete workflow"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='integration@example.com',
            email='integration@example.com',
            password='secure_integration_pass_123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            full_name='Integration User',
            user_type_code='Individual'
        )
        
        self.venue = Venue.objects.create(
            venue_name='Integration Venue',
            venue_type_code='CoworkingHub',
            address='456 Integration Ave',
            city='Integration City',
            country_code='US',
            location=Point(-73.9857, 40.7484),
            operating_hours_json={'monday': '9:00-18:00'},
            pricing_model='hourly',
            owner_user=self.user
        )
        
        self.space = Space.objects.create(
            venue=self.venue,
            space_name='Integration Space',
            capacity=6,
            hourly_rate=Decimal('25.00'),
            space_type_code='Boardroom'
        )
    
    def test_complete_booking_workflow(self):
        """Test complete booking creation workflow"""
        from django.utils import timezone
        
        booking_data = {
            'user': self.user,
            'venue': self.venue,
            'space': self.space,
            'booking_start_time': timezone.now() + timezone.timedelta(hours=1),
            'booking_end_time': timezone.now() + timezone.timedelta(hours=3),
            'booking_status_code': 'Confirmed',
            'payment_status_code': 'Paid',
            'total_price': Decimal('50.00')
        }
        
        booking = Booking.objects.create(**booking_data)
        
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.venue, self.venue)
        self.assertEqual(booking.space, self.space)
        self.assertEqual(booking.total_price, Decimal('50.00'))

@pytest.mark.security
class GlobalSecurityTests(TestCase):
    """Comprehensive security tests"""
    
    def test_user_data_encryption(self):
        """Test sensitive data encryption"""
        from core.utils.encryption import encryption
        
        sensitive_data = "sensitive_user_data_123"
        encrypted = encryption.encrypt(sensitive_data)
        decrypted = encryption.decrypt(encrypted)
        
        self.assertNotEqual(encrypted, sensitive_data)
        self.assertEqual(decrypted, sensitive_data)
    
    def test_rbac_permissions(self):
        """Test role-based access control"""
        admin_user = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='admin_pass_123'
        )
        UserProfile.objects.create(
            user=admin_user,
            full_name='Admin User',
            user_type_code='CorporateAdmin'
        )
        
        regular_user = User.objects.create_user(
            username='regular@example.com',
            email='regular@example.com',
            password='regular_pass_123'
        )
        UserProfile.objects.create(
            user=regular_user,
            full_name='Regular User',
            user_type_code='Individual'
        )
        
        # Admin should have different permissions than regular user
        self.assertEqual(admin_user.userprofile.user_type_code, 'CorporateAdmin')
        self.assertEqual(regular_user.userprofile.user_type_code, 'Individual')

@pytest.mark.performance
class GlobalPerformanceTests(TransactionTestCase):
    """Performance tests with database transactions"""
    
    def test_bulk_venue_creation(self):
        """Test bulk venue creation performance"""
        start_time = time.time()
        
        venues = []
        for i in range(50):
            venues.append(Venue(
                venue_name=f'Perf Venue {i}',
                venue_type_code='CoworkingHub',
                address=f'{i} Performance St',
                city='Performance City',
                country_code='US',
                location=Point(-74.0060 + i*0.001, 40.7128 + i*0.001),
                operating_hours_json={'monday': '9:00-18:00'},
                pricing_model='hourly'
            ))
        
        Venue.objects.bulk_create(venues)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should create 50 venues efficiently
        self.assertLess(execution_time, 2.0)
        self.assertEqual(Venue.objects.filter(venue_name__contains='Perf Venue').count(), 50)
    
    def test_geospatial_query_performance(self):
        """Test geospatial query performance"""
        # Create venues in different locations
        for i in range(20):
            Venue.objects.create(
                venue_name=f'Geo Venue {i}',
                venue_type_code='CoworkingHub',
                address=f'{i} Geo St',
                city='Geo City',
                country_code='US',
                location=Point(-74.0060 + i*0.01, 40.7128 + i*0.01),
                operating_hours_json={'monday': '9:00-18:00'},
                pricing_model='hourly'
            )
        
        start_time = time.time()
        
        # Query venues within distance
        from django.contrib.gis.measure import Distance
        center_point = Point(-74.0060, 40.7128)
        nearby_venues = Venue.objects.filter(
            location__distance_lte=(center_point, Distance(km=5))
        )
        
        # Force evaluation
        list(nearby_venues)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Geospatial query should be efficient
        self.assertLess(execution_time, 1.0)

@pytest.mark.integration
class GlobalIoTTests(TestCase):
    """IoT integration tests"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='iot@example.com',
            email='iot@example.com',
            password='iot_pass_123'
        )
        
        self.venue = Venue.objects.create(
            venue_name='IoT Venue',
            venue_type_code='CoworkingHub',
            address='789 IoT Blvd',
            city='IoT City',
            country_code='US',
            location=Point(-74.0060, 40.7128),
            operating_hours_json={'monday': '9:00-18:00'},
            pricing_model='hourly',
            owner_user=self.user
        )
        
        self.space = Space.objects.create(
            venue=self.venue,
            space_name='IoT Space',
            capacity=4,
            hourly_rate=Decimal('20.00'),
            space_type_code='Boardroom'
        )
    
    def test_sensor_data_collection(self):
        """Test IoT sensor data collection"""
        sensor = Sensor.objects.create(
            sensor_id='iot_sensor_001',
            space=self.space,
            sensor_type_code='Occupancy',
            installation_date=timezone.now().date(),
            status_code='Active'
        )
        
        # Create sensor reading
        reading = SensorReading.objects.create(
            sensor=sensor,
            reading_value=5.0,
            reading_timestamp=timezone.now(),
            data_quality_score=0.95
        )
        
        self.assertEqual(sensor.space, self.space)
        self.assertEqual(reading.sensor, sensor)
        self.assertEqual(reading.reading_value, 5.0)

@pytest.mark.slow
class GlobalEndToEndTests(TransactionTestCase):
    """End-to-end workflow tests"""
    
    def test_complete_coworking_workflow(self):
        """Test complete coworking platform workflow"""
        # 1. Create user and company
        admin_user = User.objects.create_user(
            username='workflow@example.com',
            email='workflow@example.com',
            password='workflow_pass_123'
        )
        
        profile = UserProfile.objects.create(
            user=admin_user,
            full_name='Workflow Admin',
            user_type_code='CorporateAdmin'
        )
        
        company = Company.objects.create(
            company_name='Workflow Corp',
            subscription_plan_code='Enterprise',
            billing_cycle_code='Annual',
            created_by_user=admin_user
        )
        
        # 2. Create venue and space
        venue = Venue.objects.create(
            venue_name='Workflow Venue',
            venue_type_code='CoworkingHub',
            address='999 Workflow Way',
            city='Workflow City',
            country_code='US',
            location=Point(-74.0060, 40.7128),
            operating_hours_json={'monday': '9:00-18:00'},
            pricing_model='hourly',
            owner_user=admin_user
        )
        
        space = Space.objects.create(
            venue=venue,
            space_name='Workflow Space',
            capacity=8,
            hourly_rate=Decimal('30.00'),
            space_type_code='ConferenceRoom'
        )
        
        # 3. Create booking
        from django.utils import timezone
        
        booking = Booking.objects.create(
            user=admin_user,
            venue=venue,
            space=space,
            booking_start_time=timezone.now() + timezone.timedelta(hours=1),
            booking_end_time=timezone.now() + timezone.timedelta(hours=4),
            booking_status_code='Confirmed',
            payment_status_code='Paid',
            total_price=Decimal('90.00'),
            company=company
        )
        
        # 4. Verify complete workflow
        self.assertEqual(booking.user, admin_user)
        self.assertEqual(booking.company, company)
        self.assertEqual(booking.venue, venue)
        self.assertEqual(booking.space, space)
        self.assertEqual(booking.total_price, Decimal('90.00'))
        
        # Verify relationships
        self.assertEqual(admin_user.userprofile, profile)
        self.assertEqual(company.created_by_user, admin_user)
        self.assertEqual(venue.owner_user, admin_user)