from rest_framework import permissions
from ..models import OrganizationMembership


class IsOrgAdmin(permissions.BasePermission):
    """
    Permission to check if user is an admin of the organization.
    """
    def has_object_permission(self, request, view, obj):
        # Get the organization from the object
        if hasattr(obj, 'organization'):
            organization = obj.organization
        elif obj.__class__.__name__ == 'Organization':
            organization = obj
        else:
            return False
        
        # Check if user is admin
        return OrganizationMembership.objects.filter(
            organization=organization,
            user=request.user,
            role=OrganizationMembership.Role.ADMIN
        ).exists()


class IsOrgEditor(permissions.BasePermission):
    """
    Permission to check if user is an admin or editor of the organization.
    """
    def has_object_permission(self, request, view, obj):
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
        return OrganizationMembership.objects.filter(
            organization=organization,
            user=request.user,
            role__in=[OrganizationMembership.Role.ADMIN, OrganizationMembership.Role.EDITOR]
        ).exists()


class IsOrgMember(permissions.BasePermission):
    """
    Permission to check if user is a member of the organization.
    """
    def has_object_permission(self, request, view, obj):
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
        return OrganizationMembership.objects.filter(
            organization=organization,
            user=request.user
        ).exists()


class CanManageNamespace(permissions.BasePermission):
    """
    Permission to check if user can manage namespaces (must be org admin).
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return True  # Will check at object level

    def has_object_permission(self, request, view, obj):
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


class CanManageShortURL(permissions.BasePermission):
    """
    Permission to check if user can manage short URLs (admin or editor).
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return True  # Will check at object level

    def has_object_permission(self, request, view, obj):
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

