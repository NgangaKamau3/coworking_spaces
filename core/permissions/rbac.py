from rest_framework.permissions import BasePermission
from apps.authentication.models import UserProfile

class RoleBasedPermission(BasePermission):
    """Role-based access control permission"""
    
    required_roles = []
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            profile = request.user.userprofile
            return profile.user_type_code in self.required_roles
        except UserProfile.DoesNotExist:
            return False

class IsIndividualUser(RoleBasedPermission):
    required_roles = ['Individual']

class IsCorporateAdmin(RoleBasedPermission):
    required_roles = ['CorporateAdmin']

class IsCorporateUser(RoleBasedPermission):
    required_roles = ['CorporateUser', 'CorporateAdmin']

class IsPartnerAdmin(RoleBasedPermission):
    required_roles = ['PartnerAdmin']

class IsVenueOwner(BasePermission):
    """Check if user owns the venue"""
    
    def has_object_permission(self, request, view, obj):
        return obj.owner_user_id == request.user.id