import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from rest_framework.test import APIClient
from rest_framework import status
from apps.authentication.models import UserProfile
from apps.venues.models import Venue, Space

User = get_user_model()

class VenueTestCase(TestCase):
    """Test venue management"""
    
    def setUp(self):
        self.client = APIClient()
        self.partner_user = User.objects.create_user(
            username='partner@venue.com',
            email='partner@venue.com',
            password='partnerpass123'
        )
        UserProfile.objects.create(
            user=self.partner_user,
            full_name='Partner User',
            user_type_code='PartnerAdmin'
        )
        self.client.force_authenticate(user=self.partner_user)
        
        self.venue_data = {
            'venue_name': 'Test Coworking Space',
            'venue_type_code': 'CoworkingHub',
            'address': '123 Test Street',
            'city': 'Test City',
            'country_code': 'US',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'wifi_speed_mbps': 100,
            'amenities_json': {'wifi': True, 'coffee': True},
            'operating_hours_json': {'monday': '9:00-18:00'},
            'pricing_model': 'hourly'
        }
    
    def test_venue_creation(self):
        """Test venue creation by partner admin"""
        response = self.client.post('/api/v1/venues/', self.venue_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify venue created with geospatial data
        venue = Venue.objects.get(venue_name='Test Coworking Space')
        self.assertEqual(venue.owner_user, self.partner_user)
        self.assertIsInstance(venue.location, Point)
    
    def test_venue_geospatial_search(self):
        """Test geospatial venue search"""
        # Create venue
        venue = Venue.objects.create(
            venue_name='Test Venue',
            venue_type_code='CoworkingHub',
            address='123 Test St',
            city='Test City',
            country_code='US',
            location=Point(-74.0060, 40.7128),
            operating_hours_json={'monday': '9:00-18:00'},
            pricing_model='hourly',
            owner_user=self.partner_user
        )
        
        # Search near the venue
        search_data = {
            'latitude': 40.7128,
            'longitude': -74.0060,
            'radius_km': 5.0
        }
        response = self.client.post('/api/v1/venues/search/', search_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn('distance', response.data[0])
    
    def test_venue_search_with_filters(self):
        """Test venue search with additional filters"""
        # Create venues
        Venue.objects.create(
            venue_name='Coffee Shop',
            venue_type_code='CoffeeShop',
            address='123 Coffee St',
            city='Test City',
            country_code='US',
            location=Point(-74.0060, 40.7128),
            operating_hours_json={'monday': '9:00-18:00'},
            pricing_model='hourly',
            owner_user=self.partner_user
        )
        
        Venue.objects.create(
            venue_name='Coworking Hub',
            venue_type_code='CoworkingHub',
            address='456 Work St',
            city='Test City',
            country_code='US',
            location=Point(-74.0070, 40.7138),
            operating_hours_json={'monday': '9:00-18:00'},
            pricing_model='hourly',
            owner_user=self.partner_user
        )
        
        # Search with venue type filter
        search_data = {
            'latitude': 40.7128,
            'longitude': -74.0060,
            'radius_km': 5.0,
            'venue_type': 'CoworkingHub'
        }
        response = self.client.post('/api/v1/venues/search/', search_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['venue_type_code'], 'CoworkingHub')

class SpaceTestCase(TestCase):
    """Test space management"""
    
    def setUp(self):
        self.client = APIClient()
        self.partner_user = User.objects.create_user(
            username='partner@venue.com',
            email='partner@venue.com',
            password='partnerpass123'
        )
        UserProfile.objects.create(
            user=self.partner_user,
            full_name='Partner User',
            user_type_code='PartnerAdmin'
        )
        self.client.force_authenticate(user=self.partner_user)
        
        self.venue = Venue.objects.create(
            venue_name='Test Venue',
            venue_type_code='CoworkingHub',
            address='123 Test St',
            city='Test City',
            country_code='US',
            location=Point(-74.0060, 40.7128),
            operating_hours_json={'monday': '9:00-18:00'},
            pricing_model='hourly',
            owner_user=self.partner_user
        )
    
    def test_space_creation(self):
        """Test space creation within venue"""
        space_data = {
            'space_name': 'Meeting Room A',
            'capacity': 8,
            'hourly_rate': 25.00,
            'space_type_code': 'Boardroom',
            'space_amenities_json': {'projector': True, 'whiteboard': True}
        }
        
        response = self.client.post(
            f'/api/v1/venues/{self.venue.venue_id}/spaces/',
            space_data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify space created
        space = Space.objects.get(space_name='Meeting Room A')
        self.assertEqual(space.venue, self.venue)
        self.assertEqual(space.capacity, 8)
    
    def test_space_list_for_venue(self):
        """Test listing spaces for a venue"""
        Space.objects.create(
            venue=self.venue,
            space_name='Desk 1',
            capacity=1,
            hourly_rate=10.00,
            space_type_code='SharedDesk'
        )
        
        Space.objects.create(
            venue=self.venue,
            space_name='Room 1',
            capacity=4,
            hourly_rate=20.00,
            space_type_code='PrivateRoom'
        )
        
        response = self.client.get(f'/api/v1/venues/{self.venue.venue_id}/spaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_space_update(self):
        """Test space update"""
        space = Space.objects.create(
            venue=self.venue,
            space_name='Test Space',
            capacity=2,
            hourly_rate=15.00,
            space_type_code='SharedDesk'
        )
        
        update_data = {
            'hourly_rate': 18.00,
            'capacity': 3
        }
        
        response = self.client.patch(
            f'/api/v1/venues/spaces/{space.space_id}/',
            update_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify update
        space.refresh_from_db()
        self.assertEqual(float(space.hourly_rate), 18.00)
        self.assertEqual(space.capacity, 3)