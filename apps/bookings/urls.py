from django.urls import path
from . import views

urlpatterns = [
    path('', views.BookingListCreateView.as_view(), name='booking-list'),
    path('<uuid:booking_id>/', views.BookingDetailView.as_view(), name='booking-detail'),
    path('availability/', views.check_availability, name='check-availability'),
    path('policies/', views.BookingPolicyListView.as_view(), name='booking-policies'),
    path('<uuid:booking_id>/confirm/', views.confirm_booking, name='confirm-booking'),
]