from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
import json
import hmac
import hashlib
from django.conf import settings
from .models import IoTSensor, SensorData, OccupancyEvent, BookingVerification, EnvironmentalData
from .serializers import IoTSensorSerializer, SensorDataSerializer, OccupancyEventSerializer
from apps.venues.models import Space
from apps.bookings.models import Booking

class IoTSensorListView(generics.ListCreateAPIView):
    """IoT sensor management"""
    serializer_class = IoTSensorSerializer
    
    def get_queryset(self):
        venue_id = self.request.query_params.get('venue_id')
        if venue_id:
            return IoTSensor.objects.filter(venue__venue_id=venue_id, is_active=True)
        return IoTSensor.objects.filter(is_active=True)

class SensorDataListView(generics.ListAPIView):
    """Sensor data retrieval"""
    serializer_class = SensorDataSerializer
    
    def get_queryset(self):
        sensor_id = self.kwargs.get('sensor_id')
        hours = int(self.request.query_params.get('hours', 24))
        since = timezone.now() - timezone.timedelta(hours=hours)
        
        return SensorData.objects.filter(
            sensor__sensor_id=sensor_id,
            timestamp__gte=since
        ).order_by('-timestamp')

@method_decorator(csrf_exempt, name='dispatch')
@api_view(['POST'])
@permission_classes([AllowAny])
def sensor_webhook(request):
    """Webhook endpoint for IoT sensor data"""
    
    # Verify webhook signature
    signature = request.headers.get('X-IoT-Signature')
    if not verify_iot_signature(request.body, signature):
        return Response({'error': 'Invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        payload = json.loads(request.body)
        sensor_external_id = payload.get('sensor_id')
        sensor_type = payload.get('sensor_type')
        timestamp = timezone.datetime.fromisoformat(payload.get('timestamp'))
        value = payload.get('value')
        unit = payload.get('unit', '')
        metadata = payload.get('metadata', {})
        
        # Find sensor
        try:
            sensor = IoTSensor.objects.get(
                sensor_external_id=sensor_external_id,
                is_active=True
            )
        except IoTSensor.DoesNotExist:
            return Response({'error': 'Sensor not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Update sensor heartbeat
        sensor.last_heartbeat = timezone.now()
        sensor.save()
        
        # Store sensor data
        sensor_data = SensorData.objects.create(
            sensor=sensor,
            timestamp=timestamp,
            value=value,
            unit=unit,
            metadata=metadata
        )
        
        # Process specific sensor types
        if sensor_type == 'occupancy':
            process_occupancy_data(sensor, value, timestamp, metadata)
        elif sensor_type in ['temperature', 'humidity', 'air_quality', 'noise_level']:
            process_environmental_data(sensor, sensor_type, value, timestamp)
        
        return Response({'message': 'Data processed successfully', 'data_id': sensor_data.data_id})
        
    except json.JSONDecodeError:
        return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def verify_iot_signature(payload, signature):
    """Verify IoT webhook signature"""
    if not signature:
        return False
    
    expected_signature = hmac.new(
        settings.IOT_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f'sha256={expected_signature}', signature)

def process_occupancy_data(sensor, occupancy_count, timestamp, metadata):
    """Process occupancy sensor data"""
    if not sensor.space:
        return
    
    # Create occupancy event
    event_type = 'occupancy_change'
    if metadata.get('motion_detected'):
        event_type = 'entry' if occupancy_count > 0 else 'exit'
    
    occupancy_event = OccupancyEvent.objects.create(
        space=sensor.space,
        event_type=event_type,
        occupancy_count=int(occupancy_count),
        timestamp=timestamp,
        sensor_data=metadata
    )
    
    # Check for active bookings and verify
    active_bookings = Booking.objects.filter(
        space=sensor.space,
        booking_status_code='Confirmed',
        booking_start_time__lte=timestamp,
        booking_end_time__gte=timestamp
    )
    
    for booking in active_bookings:
        verification, created = BookingVerification.objects.get_or_create(
            booking=booking,
            defaults={'verification_status': 'pending'}
        )
        
        # Update verification with occupancy event
        occupancy_event.booking = booking
        occupancy_event.save()
        
        # Trigger verification check
        verification.verify_booking_usage()

def process_environmental_data(sensor, sensor_type, value, timestamp):
    """Process environmental sensor data"""
    if not sensor.space:
        return
    
    # Get or create today's environmental data record
    date = timestamp.date()
    env_data, created = EnvironmentalData.objects.get_or_create(
        space=sensor.space,
        timestamp__date=date,
        defaults={'timestamp': timestamp}
    )
    
    # Update the appropriate field
    if sensor_type == 'temperature':
        env_data.temperature = value
    elif sensor_type == 'humidity':
        env_data.humidity = value
    elif sensor_type == 'air_quality':
        env_data.air_quality_index = int(value)
    elif sensor_type == 'noise_level':
        env_data.noise_level = value
    
    env_data.save()

@api_view(['GET'])
def space_occupancy_status(request, space_id):
    """Get real-time occupancy status for a space"""
    try:
        space = Space.objects.get(space_id=space_id)
    except Space.DoesNotExist:
        return Response({'error': 'Space not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get latest occupancy event
    latest_event = OccupancyEvent.objects.filter(space=space).first()
    
    # Get current booking
    now = timezone.now()
    current_booking = Booking.objects.filter(
        space=space,
        booking_status_code='Confirmed',
        booking_start_time__lte=now,
        booking_end_time__gte=now
    ).first()
    
    # Get environmental data
    env_data = EnvironmentalData.objects.filter(space=space).first()
    
    return Response({
        'space_id': space.space_id,
        'space_name': space.space_name,
        'current_occupancy': latest_event.occupancy_count if latest_event else 0,
        'capacity': space.capacity,
        'last_updated': latest_event.timestamp if latest_event else None,
        'current_booking': {
            'booking_id': current_booking.booking_id,
            'user_name': current_booking.user.userprofile.full_name,
            'end_time': current_booking.booking_end_time
        } if current_booking else None,
        'environmental_data': {
            'temperature': env_data.temperature,
            'humidity': env_data.humidity,
            'air_quality_index': env_data.air_quality_index,
            'noise_level': env_data.noise_level
        } if env_data else None
    })

class OccupancyEventListView(generics.ListAPIView):
    """Occupancy events for a space"""
    serializer_class = OccupancyEventSerializer
    
    def get_queryset(self):
        space_id = self.kwargs.get('space_id')
        hours = int(self.request.query_params.get('hours', 24))
        since = timezone.now() - timezone.timedelta(hours=hours)
        
        return OccupancyEvent.objects.filter(
            space__space_id=space_id,
            timestamp__gte=since
        ).order_by('-timestamp')