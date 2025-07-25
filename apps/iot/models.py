import uuid
from django.db import models
from django.utils import timezone
from apps.venues.models import Venue, Space
from apps.bookings.models import Booking

class IoTSensor(models.Model):
    """IoT sensor registration and management"""
    
    SENSOR_TYPES = [
        ('occupancy', 'Occupancy Sensor'),
        ('temperature', 'Temperature Sensor'),
        ('humidity', 'Humidity Sensor'),
        ('air_quality', 'Air Quality Sensor'),
        ('noise_level', 'Noise Level Sensor'),
    ]
    
    sensor_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    sensor_external_id = models.CharField(max_length=100, unique=True)  # External sensor ID
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='sensors')
    space = models.ForeignKey(Space, on_delete=models.CASCADE, null=True, blank=True)
    sensor_type = models.CharField(max_length=20, choices=SENSOR_TYPES)
    location_description = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['venue', 'sensor_type']),
            models.Index(fields=['space', 'sensor_type']),
        ]

class SensorData(models.Model):
    """IoT sensor data ingestion"""
    
    data_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    sensor = models.ForeignKey(IoTSensor, on_delete=models.CASCADE, related_name='data_points')
    timestamp = models.DateTimeField()
    value = models.FloatField()
    unit = models.CharField(max_length=20)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['sensor', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']

class OccupancyEvent(models.Model):
    """Real-time occupancy tracking"""
    
    EVENT_TYPES = [
        ('entry', 'Entry'),
        ('exit', 'Exit'),
        ('occupancy_change', 'Occupancy Change'),
    ]
    
    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name='occupancy_events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    occupancy_count = models.PositiveIntegerField()
    timestamp = models.DateTimeField()
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True)
    sensor_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['space', 'timestamp']),
            models.Index(fields=['booking']),
        ]
        ordering = ['-timestamp']

class BookingVerification(models.Model):
    """IoT-based booking verification"""
    
    VERIFICATION_STATUS = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('no_show', 'No Show'),
        ('early_departure', 'Early Departure'),
        ('overstay', 'Overstay'),
    ]
    
    verification_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='iot_verification')
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    occupancy_verified = models.BooleanField(default=False)
    verification_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def verify_booking_usage(self):
        """Verify booking usage based on IoT data"""
        booking = self.booking
        space = booking.space
        
        if not space:
            return
        
        # Get occupancy events during booking period
        events = OccupancyEvent.objects.filter(
            space=space,
            timestamp__range=[booking.booking_start_time, booking.booking_end_time]
        ).order_by('timestamp')
        
        if not events.exists():
            self.verification_status = 'no_show'
        else:
            first_event = events.first()
            last_event = events.last()
            
            # Check if user showed up
            if first_event.timestamp <= booking.booking_start_time + timezone.timedelta(minutes=15):
                self.actual_start_time = first_event.timestamp
                self.occupancy_verified = True
                
                # Check if user left on time
                if last_event.timestamp <= booking.booking_end_time + timezone.timedelta(minutes=15):
                    self.actual_end_time = last_event.timestamp
                    self.verification_status = 'verified'
                else:
                    self.verification_status = 'overstay'
            else:
                self.verification_status = 'no_show'
        
        self.verification_data = {
            'total_events': events.count(),
            'max_occupancy': events.aggregate(models.Max('occupancy_count'))['occupancy_count__max'] or 0,
            'verification_timestamp': timezone.now().isoformat()
        }
        
        self.save()
        
        # Update booking with IoT verification
        booking.iot_verified = True
        booking.actual_start_time = self.actual_start_time
        booking.actual_end_time = self.actual_end_time
        booking.save()

class EnvironmentalData(models.Model):
    """Environmental monitoring data"""
    
    data_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name='environmental_data')
    timestamp = models.DateTimeField()
    temperature = models.FloatField(null=True, blank=True)  # Celsius
    humidity = models.FloatField(null=True, blank=True)     # Percentage
    air_quality_index = models.IntegerField(null=True, blank=True)
    noise_level = models.FloatField(null=True, blank=True)  # Decibels
    light_level = models.FloatField(null=True, blank=True)  # Lux
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['space', 'timestamp']),
        ]
        ordering = ['-timestamp']