from rest_framework import serializers
from .models import IoTSensor, SensorData, OccupancyEvent, BookingVerification, EnvironmentalData

class IoTSensorSerializer(serializers.ModelSerializer):
    """IoT sensor serializer"""
    venue_name = serializers.CharField(source='venue.venue_name', read_only=True)
    space_name = serializers.CharField(source='space.space_name', read_only=True)
    
    class Meta:
        model = IoTSensor
        fields = ['sensor_id', 'sensor_external_id', 'venue', 'space', 'sensor_type',
                 'location_description', 'is_active', 'last_heartbeat', 'venue_name', 'space_name']
        read_only_fields = ['sensor_id', 'last_heartbeat']

class SensorDataSerializer(serializers.ModelSerializer):
    """Sensor data serializer"""
    sensor_type = serializers.CharField(source='sensor.sensor_type', read_only=True)
    
    class Meta:
        model = SensorData
        fields = ['data_id', 'timestamp', 'value', 'unit', 'metadata', 'sensor_type']
        read_only_fields = ['data_id']

class OccupancyEventSerializer(serializers.ModelSerializer):
    """Occupancy event serializer"""
    space_name = serializers.CharField(source='space.space_name', read_only=True)
    booking_user = serializers.CharField(source='booking.user.userprofile.full_name', read_only=True)
    
    class Meta:
        model = OccupancyEvent
        fields = ['event_id', 'event_type', 'occupancy_count', 'timestamp',
                 'space_name', 'booking_user', 'sensor_data']
        read_only_fields = ['event_id']

class BookingVerificationSerializer(serializers.ModelSerializer):
    """Booking verification serializer"""
    booking_details = serializers.SerializerMethodField()
    
    class Meta:
        model = BookingVerification
        fields = ['verification_id', 'verification_status', 'actual_start_time',
                 'actual_end_time', 'occupancy_verified', 'verification_data', 'booking_details']
        read_only_fields = ['verification_id']
    
    def get_booking_details(self, obj):
        return {
            'booking_id': obj.booking.booking_id,
            'venue_name': obj.booking.venue.venue_name,
            'space_name': obj.booking.space.space_name if obj.booking.space else None,
            'scheduled_start': obj.booking.booking_start_time,
            'scheduled_end': obj.booking.booking_end_time,
        }

class EnvironmentalDataSerializer(serializers.ModelSerializer):
    """Environmental data serializer"""
    space_name = serializers.CharField(source='space.space_name', read_only=True)
    
    class Meta:
        model = EnvironmentalData
        fields = ['data_id', 'timestamp', 'temperature', 'humidity', 'air_quality_index',
                 'noise_level', 'light_level', 'space_name']
        read_only_fields = ['data_id']