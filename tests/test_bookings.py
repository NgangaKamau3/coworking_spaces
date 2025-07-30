import os
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.authentication.models import UserProfile
from apps.venues.models import Venue, Space
from apps.bookings.models import Booking, BookingPolicy

User = get_user_model()

class BookingTestCase(TestCase):
    """Test booking functionality"""
    
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
        
        # Create venue and space
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
    
    def test_booking_creation_success(self):
        """Test successful booking creation"""
        start_time = timezone.now() + timezone.timedelta(hours=1)
        end_time = start_time + timezone.timedelta(hours=2)
        
        booking_data = {
            'venue': self.venue.venue_id,
            'space': self.space.space_id,
            'booking_start_time': start_time.isoformat(),
            'booking_end_time': end_time.isoformat(),
            'booking_status_code': 'Pending',
            'payment_status_code': 'Pending'
        }
        
        response = self.client.post('/api/v1/bookings/', booking_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify booking created with calculated price
        booking = Booking.objects.get(booking_id=response.data['booking_id'])
        self.assertEqual(booking.user, self.user)
        self.assertEqual(float(booking.total_price), 40.00)  # 2 hours * $20/hour
    
    def test_booking_conflict_prevention(self):
        """Test booking conflict prevention"""
        start_time = timezone.now() + timezone.timedelta(hours=1)
        end_time = start_time + timezone.timedelta(hours=2)
        
        # Create first booking
        Booking.objects.create(
            user=self.user,
            venue=self.venue,
            space=self.space,
            booking_start_time=start_time,
            booking_end_time=end_time,
            booking_status_code='Confirmed',
            payment_status_code='Paid',
            total_price=40.00
        )
        
        # Try to create conflicting booking
        conflicting_start = start_time + timezone.timedelta(minutes=30)
        conflicting_end = end_time + timezone.timedelta(minutes=30)
        
        booking_data = {
            'venue': self.venue.venue_id,
            'space': self.space.space_id,
            'booking_start_time': conflicting_start.isoformat(),
            'booking_end_time': conflicting_end.isoformat(),
            'booking_status_code': 'Pending',
            'payment_status_code': 'Pending'
        }
        
        response = self.client.post('/api/v1/bookings/', booking_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_availability_check(self):
        """Test availability checking"""
        start_time = timezone.now() + timezone.timedelta(hours=1)
        end_time = start_time + timezone.timedelta(hours=2)
        
        availability_data = {
            'venue_id': str(self.venue.venue_id),
            'space_id': str(self.space.space_id),
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        response = self.client.post('/api/v1/bookings/availability/', availability_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['available_spaces']), 1)
    
    def test_booking_policy_enforcement(self):
        """Test booking policy enforcement"""
        # Create advance booking policy
        BookingPolicy.objects.create(
            venue=self.venue,
            policy_type='advance_booking',
            policy_value={'min_hours': 24},
            active=True
        )
        
        # Try to book within 24 hours
        start_time = timezone.now() + timezone.timedelta(hours=1)
        end_time = start_time + timezone.timedelta(hours=2)
        
        booking_data = {
            'venue': self.venue.venue_id,
            'space': self.space.space_id,
            'booking_start_time': start_time.isoformat(),
            'booking_end_time': end_time.isoformat(),
            'booking_status_code': 'Pending',
            'payment_status_code': 'Pending'
        }
        
        response = self.client.post('/api/v1/bookings/', booking_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_booking_cancellation(self):
        """Test booking cancellation"""
        start_time = timezone.now() + timezone.timedelta(hours=1)
        end_time = start_time + timezone.timedelta(hours=2)
        
        booking = Booking.objects.create(
            user=self.user,
            venue=self.venue,
            space=self.space,
            booking_start_time=start_time,
            booking_end_time=end_time,
            booking_status_code='Pending',
            payment_status_code='Pending',
            total_price=40.00
        )
        
        response = self.client.delete(f'/api/v1/bookings/{booking.booking_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify booking cancelled
        booking.refresh_from_db()
        self.assertEqual(booking.booking_status_code, 'Cancelled')
    
    def test_booking_confirmation(self):
        """Test booking confirmation after payment"""
        start_time = timezone.now() + timezone.timedelta(hours=1)
        end_time = start_time + timezone.timedelta(hours=2)
        
        booking = Booking.objects.create(
            user=self.user,
            venue=self.venue,
            space=self.space,
            booking_start_time=start_time,
            booking_end_time=end_time,
            booking_status_code='Pending',
            payment_status_code='Paid',  # Payment completed
            total_price=40.00
        )
        
        response = self.client.post(f'/api/v1/bookings/{booking.booking_id}/confirm/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify booking confirmed
        booking.refresh_from_db()
        self.assertEqual(booking.booking_status_code, 'Confirmed')
    
    def test_booking_list_filtering(self):
        """Test booking list with status filtering"""
        start_time = timezone.now() + timezone.timedelta(hours=1)
        end_time = start_time + timezone.timedelta(hours=2)
        
        # Create bookings with different statuses
        Booking.objects.create(
            user=self.user,
            venue=self.venue,
            space=self.space,
            booking_start_time=start_time,
            booking_end_time=end_time,
            booking_status_code='Pending',
            payment_status_code='Pending',
            total_price=40.00
        )
        
        Booking.objects.create(
            user=self.user,
            venue=self.venue,
            space=self.space,
            booking_start_time=start_time + timezone.timedelta(hours=3),
            booking_end_time=end_time + timezone.timedelta(hours=3),
            booking_status_code='Confirmed',
            payment_status_code='Paid',
            total_price=40.00
        )
        
        # Filter by status
        response = self.client.get('/api/v1/bookings/?status=Pending')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['booking_status_code'], 'Pending')