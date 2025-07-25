from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from django_filters.rest_framework import DjangoFilterBackend
from .models import Venue, Space
from .serializers import VenueSerializer, SpaceSerializer, VenueSearchSerializer
from core.permissions.rbac import IsPartnerAdmin, IsVenueOwner

class VenueListCreateView(generics.ListCreateAPIView):
    """Venue listing and creation"""
    serializer_class = VenueSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['venue_type_code', 'city', 'active_flag']
    
    def get_queryset(self):
        return Venue.objects.filter(active_flag=True).select_related('owner_user')
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsPartnerAdmin()]
        return super().get_permissions()

class VenueDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Venue detail operations"""
    serializer_class = VenueSerializer
    lookup_field = 'venue_id'
    permission_classes = [IsVenueOwner]
    
    def get_queryset(self):
        return Venue.objects.filter(active_flag=True).prefetch_related('spaces')
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.active_flag = False
        instance.save()

@api_view(['POST'])
def venue_search(request):
    """Geospatial venue search"""
    serializer = VenueSearchSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    search_point = Point(data['longitude'], data['latitude'])
    radius = Distance(km=data['radius_km'])
    
    queryset = Venue.objects.filter(
        location__distance_lte=(search_point, radius),
        active_flag=True
    ).distance(search_point).order_by('distance')
    
    # Apply additional filters
    if data.get('venue_type'):
        queryset = queryset.filter(venue_type_code=data['venue_type'])
    
    if data.get('min_capacity'):
        queryset = queryset.filter(spaces__capacity__gte=data['min_capacity']).distinct()
    
    if data.get('amenities'):
        for amenity in data['amenities']:
            queryset = queryset.filter(amenities_json__contains={amenity: True})
    
    # Add search point to request for distance calculation
    request.search_point = search_point
    
    serializer = VenueSerializer(queryset[:20], many=True, context={'request': request})
    return Response(serializer.data)

class SpaceListCreateView(generics.ListCreateAPIView):
    """Space management within venues"""
    serializer_class = SpaceSerializer
    
    def get_queryset(self):
        venue_id = self.kwargs.get('venue_id')
        return Space.objects.filter(venue__venue_id=venue_id)
    
    def perform_create(self, serializer):
        venue_id = self.kwargs.get('venue_id')
        venue = Venue.objects.get(venue_id=venue_id)
        serializer.save(venue=venue)

class SpaceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Individual space operations"""
    serializer_class = SpaceSerializer
    lookup_field = 'space_id'
    
    def get_queryset(self):
        return Space.objects.all()