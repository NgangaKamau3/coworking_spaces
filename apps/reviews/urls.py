from django.urls import path
from . import views

urlpatterns = [
    path('', views.reviews_status, name='reviews-status'),
]