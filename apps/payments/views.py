from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from .models import Payment, PaymentAuditLog
from .serializers import PaymentSerializer, PaymentAuditLogSerializer
from .gateway import PaymentProcessor
from apps.bookings.models import Booking

class PaymentListView(generics.ListAPIView):
    """List user payments"""
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        return Payment.objects.filter(
            booking__user=self.request.user
        ).select_related('booking').order_by('-created_at')

class PaymentDetailView(generics.RetrieveAPIView):
    """Payment detail view"""
    serializer_class = PaymentSerializer
    lookup_field = 'payment_id'
    
    def get_queryset(self):
        return Payment.objects.filter(booking__user=self.request.user)

@api_view(['POST'])
def process_payment(request):
    """Enterprise-grade payment processing with idempotency and audit trails"""
    import uuid
    from decimal import Decimal
    from django.db import transaction
    from django.utils import timezone
    
    idempotency_key = request.headers.get('Idempotency-Key', str(uuid.uuid4()))
    
    # Check for duplicate requests
    existing_payment = Payment.objects.filter(
        idempotency_key=idempotency_key,
        booking__user=request.user
    ).first()
    
    if existing_payment:
        return Response(PaymentSerializer(existing_payment).data)
    
    booking_id = request.data.get('booking_id')
    payment_method = request.data.get('payment_method')
    
    try:
        booking = Booking.objects.get(
            booking_id=booking_id,
            user=request.user,
            booking_status_code='Pending'
        )
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if booking.payment_status_code == 'Paid':
        return Response({'error': 'Booking already paid'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # Create payment record with idempotency
            payment = Payment.objects.create(
                booking=booking,
                amount=booking.total_price,
                currency='USD',
                payment_method_code=payment_method,
                status_code='Pending',
                idempotency_key=idempotency_key
            )
            
            # Audit log
            PaymentAuditLog.objects.create(
                payment=payment,
                action_type='INITIATED',
                amount=payment.amount,
                reason='Payment initiated by user',
                snapshot_json={'method': payment_method, 'booking_id': str(booking_id)}
            )
            
            # Process payment through Spring gateway
            processor = PaymentProcessor()
            result = processor.process_payment(payment)
            
            # Update payment status
            payment.transaction_ref = result.get('transaction_id')
            payment.status_code = result.get('status', 'Failed')
            payment.gateway_payload = result
            payment.save()
            
            # Audit result
            PaymentAuditLog.objects.create(
                payment=payment,
                action_type=payment.status_code.upper(),
                amount=payment.amount,
                reason=f'Gateway response: {result.get("message", "")}',
                snapshot_json=result
            )
            
            if result.get('success'):
                return Response({
                    'payment_id': payment.payment_id,
                    'status': 'success',
                    'transaction_ref': payment.transaction_ref,
                    'amount': payment.amount
                })
            else:
                return Response({
                    'payment_id': payment.payment_id,
                    'status': 'failed',
                    'error': result.get('error', 'Payment processing failed')
                }, status=status.HTTP_400_BAD_REQUEST)
                
    except Exception as e:
        return Response({
            'error': 'Payment processing failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def refund_payment(request, payment_id):
    """Refund payment"""
    try:
        payment = Payment.objects.get(
            payment_id=payment_id,
            booking__user=request.user
        )
    except Payment.DoesNotExist:
        return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
    
    reason = request.data.get('reason', 'Customer requested refund')
    
    processor = PaymentProcessor()
    result = processor.refund_payment(payment, reason=reason)
    
    if result.get('success'):
        return Response({'message': 'Refund processed successfully'})
    else:
        return Response({
            'error': result.get('error', 'Refund processing failed')
        }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
@api_view(['POST'])
@permission_classes([AllowAny])
def payment_webhook(request):
    """Webhook endpoint for payment status updates from Java Spring service"""
    try:
        payload = json.loads(request.body)
        
        # Verify webhook signature (implement based on Java Spring service)
        # signature = request.headers.get('X-Webhook-Signature')
        # if not verify_webhook_signature(payload, signature):
        #     return Response({'error': 'Invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)
        
        transaction_ref = payload.get('transaction_id')
        status_update = payload.get('status')
        
        try:
            payment = Payment.objects.get(transaction_ref=transaction_ref)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Update payment status
        old_status = payment.status_code
        payment.status_code = status_update
        payment.gateway_payload.update(payload)
        payment.save()
        
        # Update booking status if needed
        if status_update == 'Paid' and payment.booking.payment_status_code != 'Paid':
            payment.booking.payment_status_code = 'Paid'
            payment.booking.save()
        elif status_update == 'Failed':
            payment.booking.payment_status_code = 'Failed'
            payment.booking.save()
        
        # Create audit log
        PaymentAuditLog.objects.create(
            payment=payment,
            action_type=status_update.upper(),
            amount=payment.amount,
            reason=f'Webhook update from {old_status} to {status_update}',
            snapshot_json=payload
        )
        
        return Response({'message': 'Webhook processed successfully'})
        
    except json.JSONDecodeError:
        return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentAuditLogView(generics.ListAPIView):
    """Payment audit log view"""
    serializer_class = PaymentAuditLogSerializer
    
    def get_queryset(self):
        payment_id = self.kwargs.get('payment_id')
        return PaymentAuditLog.objects.filter(
            payment__payment_id=payment_id,
            payment__booking__user=self.request.user
        ).order_by('-performed_at')