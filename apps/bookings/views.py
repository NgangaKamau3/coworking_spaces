from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .models import Booking, BookingPolicy
from .serializers import BookingSerializer, BookingPolicySerializer, BookingAvailabilitySerializer
from apps.venues.models import Venue, Space
from core.permissions.rbac import IsCorporateUser

class BookingListCreateView(generics.ListCreateAPIView):
    """Booking management"""
    serializer_class = BookingSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Booking.objects.filter(user=user).select_related('venue', 'space', 'company')
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(booking_status_code=status_filter)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        booking = serializer.save()
        
        # Apply venue policies
        venue = booking.venue
        policies = BookingPolicy.objects.filter(
            Q(venue=venue) | Q(space=booking.space),
            active=True
        )
        
        for policy in policies:
            policy.apply_policy(booking)

class BookingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Individual booking operations"""
    serializer_class = BookingSerializer
    lookup_field = 'booking_id'
    
    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        booking = self.get_object()
        
        # Only allow updates if booking is pending
        if booking.booking_status_code != 'Pending':
            raise serializers.ValidationError("Cannot modify confirmed booking")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        # Cancel booking instead of deleting
        instance.booking_status_code = 'Cancelled'
        instance.save()

@api_view(['POST'])
def check_availability(request):
    """Check space availability"""
    serializer = BookingAvailabilitySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    try:
        venue = Venue.objects.get(venue_id=data['venue_id'])
    except Venue.DoesNotExist:
        return Response({'error': 'Venue not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check specific space or all spaces in venue
    if data.get('space_id'):
        spaces = Space.objects.filter(space_id=data['space_id'], venue=venue)
    else:
        spaces = venue.spaces.filter(availability_status='Available')
    
    available_spaces = []
    
    for space in spaces:
        conflicts = Booking.objects.filter(
            space=space,
            booking_status_code__in=['Pending', 'Confirmed'],
            booking_start_time__lt=data['end_time'],
            booking_end_time__gt=data['start_time']
        )
        
        if not conflicts.exists():
            available_spaces.append({
                'space_id': space.space_id,
                'space_name': space.space_name,
                'capacity': space.capacity,
                'hourly_rate': space.hourly_rate,
                'daily_rate': space.daily_rate,
            })
    
    return Response({
        'venue_id': venue.venue_id,
        'venue_name': venue.venue_name,
        'available_spaces': available_spaces,
        'total_available': len(available_spaces)
    })

class BookingPolicyListView(generics.ListCreateAPIView):
    """Booking policy management"""
    serializer_class = BookingPolicySerializer
    
    def get_queryset(self):
        venue_id = self.request.query_params.get('venue_id')
        if venue_id:
            return BookingPolicy.objects.filter(venue__venue_id=venue_id, active=True)
        return BookingPolicy.objects.filter(active=True)

@api_view(['POST'])
def confirm_booking(request, booking_id):
    """Confirm a pending booking"""
    try:
        booking = Booking.objects.get(
            booking_id=booking_id,
            user=request.user,
            booking_status_code='Pending'
        )
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check payment status
    if booking.payment_status_code != 'Paid':
        return Response({'error': 'Payment required before confirmation'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    booking.booking_status_code = 'Confirmed'
    booking.save()
    
    return Response({'message': 'Booking confirmed successfully'})