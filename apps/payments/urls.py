from django.urls import path
from . import views

urlpatterns = [
    path('', views.PaymentListView.as_view(), name='payment-list'),
    path('<uuid:payment_id>/', views.PaymentDetailView.as_view(), name='payment-detail'),
    path('process/', views.process_payment, name='process-payment'),
    path('<uuid:payment_id>/refund/', views.refund_payment, name='refund-payment'),
    path('webhook/', views.payment_webhook, name='payment-webhook'),
    path('<uuid:payment_id>/audit/', views.PaymentAuditLogView.as_view(), name='payment-audit'),
]