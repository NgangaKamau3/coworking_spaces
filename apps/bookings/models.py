import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.authentication.models import User, Company
from apps.venues.models import Venue, Space

class Booking(models.Model):
    """Booking model with conflict resolution"""
    
    BOOKING_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]
    
    booking_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    space = models.ForeignKey(Space, on_delete=models.SET_NULL, null=True, blank=True)
    booking_start_time = models.DateTimeField()
    booking_end_time = models.DateTimeField()
    booking_status_code = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status_code = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # IoT verification
    iot_verified = models.BooleanField(default=False)
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'booking'
        indexes = [
            models.Index(fields=['user', 'booking_start_time']),
            models.Index(fields=['venue', 'booking_start_time']),
            models.Index(fields=['space']),
        ]
    
    def clean(self):
        if self.booking_end_time <= self.booking_start_time:
            raise ValidationError("End time must be after start time")
        
        # Check for conflicts
        conflicts = Booking.objects.filter(
            space=self.space,
            booking_status_code__in=['Pending', 'Confirmed'],
            booking_start_time__lt=self.booking_end_time,
            booking_end_time__gt=self.booking_start_time
        ).exclude(booking_id=self.booking_id)
        
        if conflicts.exists():
            raise ValidationError("Booking conflicts with existing reservation")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def calculate_price(self):
        """Calculate booking price based on duration and rates"""
        if not self.space:
            return 0
        
        duration_hours = (self.booking_end_time - self.booking_start_time).total_seconds() / 3600
        
        if self.space.hourly_rate:
            return float(self.space.hourly_rate) * duration_hours
        elif self.space.daily_rate and duration_hours >= 8:
            days = max(1, int(duration_hours / 8))
            return float(self.space.daily_rate) * days
        
        return 0

class BookingParticipant(models.Model):
    """Booking participants for group bookings"""
    
    booking_participant_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    guest_email = models.EmailField(blank=True)
    invited_flag = models.BooleanField(default=False)
    checked_in_flag = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'booking_participant'

class BookingPolicy(models.Model):
    """Booking policies and restrictions"""
    
    POLICY_TYPES = [
        ('cancellation', 'Cancellation Policy'),
        ('advance_booking', 'Advance Booking'),
        ('max_duration', 'Maximum Duration'),
        ('corporate_only', 'Corporate Only'),
    ]
    
    policy_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='policies')
    space = models.ForeignKey(Space, on_delete=models.CASCADE, null=True, blank=True)
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPES)
    policy_value = models.JSONField()  # Flexible policy configuration
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def apply_policy(self, booking):
        """Apply policy to booking"""
        if self.policy_type == 'advance_booking':
            min_hours = self.policy_value.get('min_hours', 0)
            if (booking.booking_start_time - timezone.now()).total_seconds() < min_hours * 3600:
                raise ValidationError(f"Booking must be made at least {min_hours} hours in advance")
        
        elif self.policy_type == 'max_duration':
            max_hours = self.policy_value.get('max_hours', 24)
            duration = (booking.booking_end_time - booking.booking_start_time).total_seconds() / 3600
            if duration > max_hours:
                raise ValidationError(f"Maximum booking duration is {max_hours} hours")
        
        elif self.policy_type == 'corporate_only':
            if not booking.company:
                raise ValidationError("This space is only available for corporate bookings")