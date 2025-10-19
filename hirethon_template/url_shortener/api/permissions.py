from rest_framework import permissions
from ..models import OrganizationMembership


class IsOrgAdmin(permissions.BasePermission):
    """
    Permission to check if user is an admin of the organization.
    """
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # For list views, we need to check if user is admin of any organization
        # or if the view has an organization attribute
        if hasattr(view, 'organization') and view.organization:
            try:
                return OrganizationMembership.objects.filter(
                    organization=view.organization,
                    user=request.user,
                    role=OrganizationMembership.Role.ADMIN
                ).exists()
            except (TypeError, ValueError):
                # Handle cases where organization is not a valid Organization instance
                return False
        
        # For object-level permissions, we need to check if user is admin of the object's organization
        # This will be called by has_object_permission
        return True
    
    def has_object_permission(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get the organization from the object
        if hasattr(obj, 'organization'):
            organization = obj.organization
        elif obj.__class__.__name__ == 'Organization':
            organization = obj
        else:
            return False
        
        # Check if user is admin
        try:
            return OrganizationMembership.objects.filter(
                organization=organization,
                user=request.user,
                role=OrganizationMembership.Role.ADMIN
            ).exists()
        except (TypeError, ValueError):
            # Handle cases where organization or user is invalid
            return False


class IsOrgEditor(permissions.BasePermission):
    """
    Permission to check if user is an admin or editor of the organization.
    """
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # For list views, we need to check if user is admin or editor of any organization
        # or if the view has an organization attribute
        if hasattr(view, 'organization') and view.organization:
            try:
                return OrganizationMembership.objects.filter(
                    organization=view.organization,
                    user=request.user,
                    role__in=[OrganizationMembership.Role.ADMIN, OrganizationMembership.Role.EDITOR]
                ).exists()
            except (TypeError, ValueError):
                # Handle cases where organization is not a valid Organization instance
                return False
        return False
    
    def has_object_permission(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get the organization from the object
        if hasattr(obj, 'organization'):
            organization = obj.organization
        elif hasattr(obj, 'namespace'):
            organization = obj.namespace.organization
        elif obj.__class__.__name__ == 'Organization':
            organization = obj
        else:
            return False
        
        # Check if user is admin or editor
        try:
            return OrganizationMembership.objects.filter(
                organization=organization,
                user=request.user,
                role__in=[OrganizationMembership.Role.ADMIN, OrganizationMembership.Role.EDITOR]
            ).exists()
        except (TypeError, ValueError):
            # Handle cases where organization or user is invalid
            return False


class IsOrgMember(permissions.BasePermission):
    """
    Permission to check if user is a member of the organization.
    """
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # For list views, we need to check if user is a member of any organization
        # or if the view has an organization attribute
        if hasattr(view, 'organization') and view.organization:
            try:
                return OrganizationMembership.objects.filter(
                    organization=view.organization,
                    user=request.user
                ).exists()
            except (TypeError, ValueError):
                # Handle cases where organization is not a valid Organization instance
                return False
        return False
    
    def has_object_permission(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get the organization from the object
        if hasattr(obj, 'organization'):
            organization = obj.organization
        elif hasattr(obj, 'namespace'):
            organization = obj.namespace.organization
        elif obj.__class__.__name__ == 'Organization':
            organization = obj
        else:
            return False
        
        # Check if user is any member
        try:
            return OrganizationMembership.objects.filter(
                organization=organization,
                user=request.user
            ).exists()
        except (TypeError, ValueError):
            # Handle cases where organization or user is invalid
            return False


class CanManageNamespace(permissions.BasePermission):
    """
    Permission to check if user can manage namespaces (must be org admin).
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return True  # Will check at object level

    def has_object_permission(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            if request.method in permissions.SAFE_METHODS:
                # Any member can view
                return OrganizationMembership.objects.filter(
                    organization=obj.organization,
                    user=request.user
                ).exists()
            else:
                # Only admins can create/update/delete
                return OrganizationMembership.objects.filter(
                    organization=obj.organization,
                    user=request.user,
                    role=OrganizationMembership.Role.ADMIN
                ).exists()
        except (TypeError, ValueError, AttributeError):
            # Handle cases where organization or user is invalid
            return False


class CanManageShortURL(permissions.BasePermission):
    """
    Permission to check if user can manage short URLs (admin or editor).
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return True  # Will check at object level

    def has_object_permission(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            organization = obj.namespace.organization
            
            if request.method in permissions.SAFE_METHODS:
                # Any member can view
                return OrganizationMembership.objects.filter(
                    organization=organization,
                    user=request.user
                ).exists()
            else:
                # Admins and editors can create/update/delete
                return OrganizationMembership.objects.filter(
                    organization=organization,
                    user=request.user,
                    role__in=[OrganizationMembership.Role.ADMIN, OrganizationMembership.Role.EDITOR]
                ).exists()
        except (TypeError, ValueError, AttributeError):
            # Handle cases where organization or user is invalid
            return False

