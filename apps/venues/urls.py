from django.urls import path
from . import views

urlpatterns = [
    path('', views.VenueListCreateView.as_view(), name='venue-list'),
    path('<uuid:venue_id>/', views.VenueDetailView.as_view(), name='venue-detail'),
    path('search/', views.venue_search, name='venue-search'),
    path('<uuid:venue_id>/spaces/', views.SpaceListCreateView.as_view(), name='space-list'),
    path('spaces/<uuid:space_id>/', views.SpaceDetailView.as_view(), name='space-detail'),
]