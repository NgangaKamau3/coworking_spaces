from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from oauth2_provider.models import Application, AccessToken
from django.contrib.auth import authenticate
from .models import User, UserProfile, Company
from .serializers import UserRegistrationSerializer, UserProfileSerializer, CompanySerializer
from core.permissions.rbac import IsCorporateAdmin

class UserRegistrationView(generics.CreateAPIView):
    """User registration endpoint"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile management"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user.userprofile

class CompanyListCreateView(generics.ListCreateAPIView):
    """Company management for corporate admins"""
    serializer_class = CompanySerializer
    permission_classes = [IsCorporateAdmin]
    
    def get_queryset(self):
        return Company.objects.filter(active_flag=True)
    
    def perform_create(self, serializer):
        serializer.save(created_by_user=self.request.user)

@api_view(['POST'])
@permission_classes([AllowAny])
def oauth_token(request):
    """OAuth2 token endpoint"""
    email = request.data.get('email')
    password = request.data.get('password')
    
    user = authenticate(username=email, password=password)
    if not user:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Get or create OAuth2 application
    try:
        application = Application.objects.get(name='coworking_platform')
    except Application.DoesNotExist:
        return Response({'error': 'OAuth2 application not configured'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Create access token
    access_token = AccessToken.objects.create(
        user=user,
        application=application,
        scope='read write'
    )
    
    return Response({
        'access_token': access_token.token,
        'token_type': 'Bearer',
        'expires_in': 3600,
        'scope': 'read write'
    })