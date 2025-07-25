import uuid
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from apps.authentication.models import User

class Venue(models.Model):
    VENUE_TYPES = [
        ('CoffeeShop', 'Coffee Shop'),
        ('Hotel', 'Hotel'),
        ('CoworkingHub', 'Coworking Hub'),
    ]
    
    venue_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    venue_name = models.CharField(max_length=255)
    venue_type_code = models.CharField(max_length=20, choices=VENUE_TYPES)
    owner_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    country_code = models.CharField(max_length=2)
    location = models.PointField(geography=True)
    wifi_speed_mbps = models.IntegerField(null=True, blank=True)
    amenities_json = models.JSONField(default=dict)
    operating_hours_json = models.JSONField()
    pricing_model = models.CharField(max_length=50)
    active_flag = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'venue'
        indexes = [
            models.Index(fields=['venue_type_code']),
            models.Index(fields=['active_flag']),
        ]

class Space(models.Model):
    SPACE_TYPES = [
        ('SharedDesk', 'Shared Desk'),
        ('PrivateRoom', 'Private Room'),
        ('Boardroom', 'Boardroom'),
    ]
    
    AVAILABILITY_STATUS = [
        ('Available', 'Available'),
        ('Occupied', 'Occupied'),
        ('Maintenance', 'Maintenance'),
    ]
    
    space_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='spaces')
    space_name = models.CharField(max_length=255)
    capacity = models.PositiveIntegerField()
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_STATUS, default='Available')
    space_amenities_json = models.JSONField(default=dict)
    space_type_code = models.CharField(max_length=20, choices=SPACE_TYPES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'space'