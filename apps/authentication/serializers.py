from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UserProfile, Company

class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField()
    user_type_code = serializers.ChoiceField(choices=UserProfile.USER_TYPE_CHOICES)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'full_name', 'user_type_code', 'phone_number']
    
    def create(self, validated_data):
        full_name = validated_data.pop('full_name')
        user_type_code = validated_data.pop('user_type_code')
        
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            phone_number=validated_data.get('phone_number', '')
        )
        
        UserProfile.objects.create(
            user=user,
            full_name=full_name,
            user_type_code=user_type_code,
            phone_number=validated_data.get('phone_number', '')
        )
        
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    
    class Meta:
        model = UserProfile
        fields = ['user_id', 'full_name', 'user_type_code', 'preferred_language', 
                 'profile_picture_url', 'account_status_code', 'phone_number']
        read_only_fields = ['user_id']

class CompanySerializer(serializers.ModelSerializer):
    """Company serializer"""
    
    class Meta:
        model = Company
        fields = ['company_id', 'company_name', 'subscription_plan_code', 
                 'billing_cycle_code', 'active_flag']
        read_only_fields = ['company_id']