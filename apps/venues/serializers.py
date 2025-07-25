from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.gis.geos import Point
from .models import Venue, Space

class SpaceSerializer(serializers.ModelSerializer):
    """Space serializer"""
    
    class Meta:
        model = Space
        fields = ['space_id', 'space_name', 'capacity', 'hourly_rate', 'daily_rate',
                 'availability_status', 'space_amenities_json', 'space_type_code']
        read_only_fields = ['space_id']

class VenueSerializer(GeoFeatureModelSerializer):
    """Venue serializer with geospatial support"""
    spaces = SpaceSerializer(many=True, read_only=True)
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)
    distance = serializers.SerializerMethodField()
    
    class Meta:
        model = Venue
        geo_field = 'location'
        fields = ['venue_id', 'venue_name', 'venue_type_code', 'address', 'city',
                 'country_code', 'wifi_speed_mbps', 'amenities_json', 'operating_hours_json',
                 'pricing_model', 'active_flag', 'spaces', 'latitude', 'longitude', 'distance']
        read_only_fields = ['venue_id', 'distance']
    
    def create(self, validated_data):
        latitude = validated_data.pop('latitude')
        longitude = validated_data.pop('longitude')
        venue = Venue.objects.create(
            location=Point(longitude, latitude),
            owner_user=self.context['request'].user,
            **validated_data
        )
        return venue
    
    def get_distance(self, obj):
        """Calculate distance from search point if provided"""
        request = self.context.get('request')
        if request and hasattr(request, 'search_point'):
            return obj.location.distance(request.search_point) * 111000  # Convert to meters
        return None

class VenueSearchSerializer(serializers.Serializer):
    """Venue search parameters"""
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    radius_km = serializers.FloatField(default=10.0)
    venue_type = serializers.ChoiceField(choices=Venue.VENUE_TYPES, required=False)
    min_capacity = serializers.IntegerField(required=False)
    amenities = serializers.ListField(child=serializers.CharField(), required=False)