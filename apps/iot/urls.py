from django.urls import path
from . import views

urlpatterns = [
    path('sensors/', views.IoTSensorListView.as_view(), name='iot-sensor-list'),
    path('sensors/<uuid:sensor_id>/data/', views.SensorDataListView.as_view(), name='sensor-data'),
    path('webhook/', views.sensor_webhook, name='iot-webhook'),
    path('spaces/<uuid:space_id>/occupancy/', views.space_occupancy_status, name='space-occupancy'),
    path('spaces/<uuid:space_id>/events/', views.OccupancyEventListView.as_view(), name='occupancy-events'),
]