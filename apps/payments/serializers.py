from rest_framework import serializers
from .models import Payment, PaymentAuditLog, PaymentGatewayConfig

class PaymentSerializer(serializers.ModelSerializer):
    """Payment serializer"""
    booking_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = ['payment_id', 'amount', 'currency', 'payment_method_code',
                 'transaction_ref', 'payment_timestamp', 'status_code',
                 'card_last4', 'booking_details']
        read_only_fields = ['payment_id', 'payment_timestamp']
    
    def get_booking_details(self, obj):
        return {
            'booking_id': obj.booking.booking_id,
            'venue_name': obj.booking.venue.venue_name,
            'space_name': obj.booking.space.space_name if obj.booking.space else None,
            'booking_start_time': obj.booking.booking_start_time,
            'booking_end_time': obj.booking.booking_end_time,
        }

class PaymentAuditLogSerializer(serializers.ModelSerializer):
    """Payment audit log serializer"""
    performed_by_name = serializers.CharField(source='performed_by_user.userprofile.full_name', read_only=True)
    
    class Meta:
        model = PaymentAuditLog
        fields = ['audit_id', 'action_type', 'amount', 'reason', 'performed_at',
                 'performed_by_name', 'snapshot_json']
        read_only_fields = ['audit_id', 'performed_at']

class PaymentGatewayConfigSerializer(serializers.ModelSerializer):
    """Payment gateway configuration serializer"""
    
    class Meta:
        model = PaymentGatewayConfig
        fields = ['config_id', 'gateway_type', 'gateway_name', 'endpoint_url',
                 'is_active', 'config_json']
        read_only_fields = ['config_id']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Don't expose sensitive configuration
        if 'api_key' in data.get('config_json', {}):
            data['config_json'] = {k: v for k, v in data['config_json'].items() 
                                 if k not in ['api_key', 'secret_key']}
        return data