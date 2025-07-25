from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('companies/', views.CompanyListCreateView.as_view(), name='company-list'),
    path('token/', views.oauth_token, name='oauth-token'),
]