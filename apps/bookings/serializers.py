from rest_framework import serializers
from django.utils import timezone
from .models import Booking, BookingParticipant, BookingPolicy
from apps.venues.serializers import VenueSerializer, SpaceSerializer

class BookingParticipantSerializer(serializers.ModelSerializer):
    """Booking participant serializer"""
    
    class Meta:
        model = BookingParticipant
        fields = ['booking_participant_id', 'user', 'guest_email', 'invited_flag', 'checked_in_flag']
        read_only_fields = ['booking_participant_id']

class BookingSerializer(serializers.ModelSerializer):
    """Booking serializer with validation"""
    participants = BookingParticipantSerializer(many=True, read_only=True)
    venue_details = VenueSerializer(source='venue', read_only=True)
    space_details = SpaceSerializer(source='space', read_only=True)
    duration_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = ['booking_id', 'venue', 'space', 'booking_start_time', 'booking_end_time',
                 'booking_status_code', 'total_price', 'payment_status_code', 'company',
                 'iot_verified', 'actual_start_time', 'actual_end_time', 'participants',
                 'venue_details', 'space_details', 'duration_hours']
        read_only_fields = ['booking_id', 'total_price', 'iot_verified']
    
    def validate(self, data):
        """Validate booking data"""
        if data['booking_end_time'] <= data['booking_start_time']:
            raise serializers.ValidationError("End time must be after start time")
        
        if data['booking_start_time'] <= timezone.now():
            raise serializers.ValidationError("Booking cannot be in the past")
        
        # Check space belongs to venue
        if data.get('space') and data['space'].venue != data['venue']:
            raise serializers.ValidationError("Space does not belong to the selected venue")
        
        return data
    
    def create(self, validated_data):
        booking = Booking.objects.create(
            user=self.context['request'].user,
            **validated_data
        )
        
        # Calculate and set price
        booking.total_price = booking.calculate_price()
        booking.save()
        
        return booking
    
    def get_duration_hours(self, obj):
        """Calculate booking duration in hours"""
        return (obj.booking_end_time - obj.booking_start_time).total_seconds() / 3600

class BookingPolicySerializer(serializers.ModelSerializer):
    """Booking policy serializer"""
    
    class Meta:
        model = BookingPolicy
        fields = ['policy_id', 'venue', 'space', 'policy_type', 'policy_value', 'active']
        read_only_fields = ['policy_id']

class BookingAvailabilitySerializer(serializers.Serializer):
    """Check availability serializer"""
    venue_id = serializers.UUIDField()
    space_id = serializers.UUIDField(required=False)
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    
    def validate(self, data):
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError("End time must be after start time")
        
        if data['start_time'] <= timezone.now():
            raise serializers.ValidationError("Start time cannot be in the past")
        
        return data