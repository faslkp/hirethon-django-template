import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from rest_framework.test import APIRequestFactory

from hirethon_template.url_shortener.api.permissions import (
    IsOrgAdmin,
    IsOrgEditor,
    IsOrgMember,
)
from hirethon_template.url_shortener.models import Organization, OrganizationMembership
from .factories import (
    OrganizationFactory,
    AdminMembershipFactory,
    EditorMembershipFactory,
    ViewerMembershipFactory,
    UserFactory,
)

User = get_user_model()


class TestIsOrgAdmin(TestCase):
    """Test IsOrgAdmin permission class"""
    
    def setUp(self):
        """Set up test environment"""
        self.factory = APIRequestFactory()
        self.permission = IsOrgAdmin()
        
        # Create test users and organization
        self.user = UserFactory()
        self.organization = OrganizationFactory(created_by=self.user)
        
        # Create users with different roles
        self.admin_user = UserFactory()
        self.editor_user = UserFactory()
        self.viewer_user = UserFactory()
        self.non_member_user = UserFactory()
        
        # Create memberships
        AdminMembershipFactory(organization=self.organization, user=self.admin_user)
        EditorMembershipFactory(organization=self.organization, user=self.editor_user)
        ViewerMembershipFactory(organization=self.organization, user=self.viewer_user)
        # Add organization creator as admin
        AdminMembershipFactory(organization=self.organization, user=self.user)
    
    def test_admin_has_permission(self):
        """Test that admin user has permission"""
        request = self.factory.get('/')
        request.user = self.admin_user
        
        # Mock the view to have organization attribute
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        view = MockView(self.organization)
        
        assert self.permission.has_permission(request, view) is True
    
    def test_editor_has_no_permission(self):
        """Test that editor user does not have permission"""
        request = self.factory.get('/')
        request.user = self.editor_user
        
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        view = MockView(self.organization)
        
        assert self.permission.has_permission(request, view) is False
    
    def test_viewer_has_no_permission(self):
        """Test that viewer user does not have permission"""
        request = self.factory.get('/')
        request.user = self.viewer_user
        
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        view = MockView(self.organization)
        
        assert self.permission.has_permission(request, view) is False
    
    def test_non_member_has_no_permission(self):
        """Test that non-member user does not have permission"""
        request = self.factory.get('/')
        request.user = self.non_member_user
        
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        view = MockView(self.organization)
        
        assert self.permission.has_permission(request, view) is False
    
    def test_anonymous_user_has_no_permission(self):
        """Test that anonymous user does not have permission"""
        request = self.factory.get('/')
        request.user = None
        
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        view = MockView(self.organization)
        
        assert self.permission.has_permission(request, view) is False
    
    def test_organization_creator_has_permission(self):
        """Test that organization creator has permission"""
        request = self.factory.get('/')
        request.user = self.user  # Organization creator
        
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        view = MockView(self.organization)
        
        assert self.permission.has_permission(request, view) is True
    
    def test_view_without_organization_attribute(self):
        """Test that view without organization attribute returns False"""
        request = self.factory.get('/')
        request.user = self.admin_user
        
        class MockView:
            pass  # No organization attribute
        
        view = MockView()
        
        assert self.permission.has_permission(request, view) is False
    
    def test_view_with_none_organization(self):
        """Test that view with None organization returns False"""
        request = self.factory.get('/')
        request.user = self.admin_user
        
        class MockView:
            def __init__(self):
                self.organization = None
        
        view = MockView()
        
        assert self.permission.has_permission(request, view) is False


class TestIsOrgEditor(TestCase):
    """Test IsOrgEditor permission class"""
    
    def setUp(self):
        """Set up test environment"""
        self.factory = APIRequestFactory()
        self.permission = IsOrgEditor()
        
        # Create test users and organization
        self.user = UserFactory()
        self.organization = OrganizationFactory(created_by=self.user)
        
        # Create users with different roles
        self.admin_user = UserFactory()
        self.editor_user = UserFactory()
        self.viewer_user = UserFactory()
        self.non_member_user = UserFactory()
        
        # Create memberships
        AdminMembershipFactory(organization=self.organization, user=self.admin_user)
        EditorMembershipFactory(organization=self.organization, user=self.editor_user)
        ViewerMembershipFactory(organization=self.organization, user=self.viewer_user)
        # Add organization creator as admin
        AdminMembershipFactory(organization=self.organization, user=self.user)
    
    def test_admin_has_permission(self):
        """Test that admin user has permission"""
        request = self.factory.get('/')
        request.user = self.admin_user
        
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        view = MockView(self.organization)
        
        assert self.permission.has_permission(request, view) is True
    
    def test_editor_has_permission(self):
        """Test that editor user has permission"""
        request = self.factory.get('/')
        request.user = self.editor_user
        
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        view = MockView(self.organization)
        
        assert self.permission.has_permission(request, view) is True
    
    def test_viewer_has_no_permission(self):
        """Test that viewer user does not have permission"""
        request = self.factory.get('/')
        request.user = self.viewer_user
        
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        view = MockView(self.organization)
        
        assert self.permission.has_permission(request, view) is False
    
    def test_non_member_has_no_permission(self):
        """Test that non-member user does not have permission"""
        request = self.factory.get('/')
        request.user = self.non_member_user
        
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        view = MockView(self.organization)
        
        assert self.permission.has_permission(request, view) is False
    
    def test_organization_creator_has_permission(self):
        """Test that organization creator has permission"""
        request = self.factory.get('/')
        request.user = self.user  # Organization creator
        
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        view = MockView(self.organization)
        
        assert self.permission.has_permission(request, view) is True
    
    def test_view_without_organization_attribute(self):
        """Test that view without organization attribute returns False"""
        request = self.factory.get('/')
        request.user = self.editor_user
        
        class MockView:
            pass  # No organization attribute
        
        view = MockView()
        
        assert self.permission.has_permission(request, view) is False
    
    def test_view_with_none_organization(self):
        """Test that view with None organization returns False"""
        request = self.factory.get('/')
        request.user = self.editor_user
        
        class MockView:
            def __init__(self):
                self.organization = None
        
        view = MockView()
        
        assert self.permission.has_permission(request, view) is False


class TestIsOrgMember(TestCase):
    """Test IsOrgMember permission class"""
    
    def setUp(self):
        """Set up test environment"""
        self.factory = APIRequestFactory()
        self.permission = IsOrgMember()
        
        # Create test users and organization
        self.user = UserFactory()
        self.organization = OrganizationFactory(created_by=self.user)
        
        # Create users with different roles
        self.admin_user = UserFactory()
        self.editor_user = UserFactory()
        self.viewer_user = UserFactory()
        self.non_member_user = UserFactory()
        
        # Create memberships
        AdminMembershipFactory(organization=self.organization, user=self.admin_user)
        EditorMembershipFactory(organization=self.organization, user=self.editor_user)
        ViewerMembershipFactory(organization=self.organization, user=self.viewer_user)
        # Add organization creator as admin
        AdminMembershipFactory(organization=self.organization, user=self.user)
    
    def test_admin_has_permission(self):
        """Test that admin user has permission"""
        request = self.factory.get('/')
        request.user = self.admin_user
        
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        view = MockView(self.organization)
        
        assert self.permission.has_permission(request, view) is True
    
    def test_editor_has_permission(self):
        """Test that editor user has permission"""
        request = self.factory.get('/')
        request.user = self.editor_user
        
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        view = MockView(self.organization)
        
        assert self.permission.has_permission(request, view) is True
    
    def test_viewer_has_permission(self):
        """Test that viewer user has permission"""
        request = self.factory.get('/')
        request.user = self.viewer_user
        
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        view = MockView(self.organization)
        
        assert self.permission.has_permission(request, view) is True
    
    def test_non_member_has_no_permission(self):
        """Test that non-member user does not have permission"""
        request = self.factory.get('/')
        request.user = self.non_member_user
        
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        view = MockView(self.organization)
        
        assert self.permission.has_permission(request, view) is False
    
    def test_organization_creator_has_permission(self):
        """Test that organization creator has permission"""
        request = self.factory.get('/')
        request.user = self.user  # Organization creator
        
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        view = MockView(self.organization)
        
        assert self.permission.has_permission(request, view) is True
    
    def test_anonymous_user_has_no_permission(self):
        """Test that anonymous user does not have permission"""
        request = self.factory.get('/')
        request.user = None
        
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        view = MockView(self.organization)
        
        assert self.permission.has_permission(request, view) is False
    
    def test_view_without_organization_attribute(self):
        """Test that view without organization attribute returns False"""
        request = self.factory.get('/')
        request.user = self.viewer_user
        
        class MockView:
            pass  # No organization attribute
        
        view = MockView()
        
        assert self.permission.has_permission(request, view) is False
    
    def test_view_with_none_organization(self):
        """Test that view with None organization returns False"""
        request = self.factory.get('/')
        request.user = self.viewer_user
        
        class MockView:
            def __init__(self):
                self.organization = None
        
        view = MockView()
        
        assert self.permission.has_permission(request, view) is False


class TestPermissionIntegration(TestCase):
    """Test permission classes with real view objects"""
    
    def setUp(self):
        """Set up test environment"""
        self.factory = APIRequestFactory()
        
        # Create test users and organization
        self.user = UserFactory()
        self.organization = OrganizationFactory(created_by=self.user)
        
        # Create users with different roles
        self.admin_user = UserFactory()
        self.editor_user = UserFactory()
        self.viewer_user = UserFactory()
        self.non_member_user = UserFactory()
        
        # Create memberships
        AdminMembershipFactory(organization=self.organization, user=self.admin_user)
        EditorMembershipFactory(organization=self.organization, user=self.editor_user)
        ViewerMembershipFactory(organization=self.organization, user=self.viewer_user)
    
    def test_permission_hierarchy(self):
        """Test that permission hierarchy works correctly"""
        # Admin should have all permissions
        admin_request = self.factory.get('/')
        admin_request.user = self.admin_user
        
        # Editor should have editor and member permissions
        editor_request = self.factory.get('/')
        editor_request.user = self.editor_user
        
        # Viewer should only have member permission
        viewer_request = self.factory.get('/')
        viewer_request.user = self.viewer_user
        
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        view = MockView(self.organization)
        
        # Test admin permissions
        assert IsOrgAdmin().has_permission(admin_request, view) is True
        assert IsOrgEditor().has_permission(admin_request, view) is True
        assert IsOrgMember().has_permission(admin_request, view) is True
        
        # Test editor permissions
        assert IsOrgAdmin().has_permission(editor_request, view) is False
        assert IsOrgEditor().has_permission(editor_request, view) is True
        assert IsOrgMember().has_permission(editor_request, view) is True
        
        # Test viewer permissions
        assert IsOrgAdmin().has_permission(viewer_request, view) is False
        assert IsOrgEditor().has_permission(viewer_request, view) is False
        assert IsOrgMember().has_permission(viewer_request, view) is True
    
    def test_permission_with_different_organizations(self):
        """Test that permissions work correctly across different organizations"""
        # Create another organization
        other_org = OrganizationFactory(created_by=self.non_member_user)
        
        # Make admin_user a member of other_org
        AdminMembershipFactory(organization=other_org, user=self.admin_user)
        
        request = self.factory.get('/')
        request.user = self.admin_user
        
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        # Test with original organization (admin_user is admin)
        view1 = MockView(self.organization)
        assert IsOrgAdmin().has_permission(request, view1) is True
        
        # Test with other organization (admin_user is admin there too)
        view2 = MockView(other_org)
        assert IsOrgAdmin().has_permission(request, view2) is True
    
    def test_permission_with_no_organization(self):
        """Test that permissions handle missing organization gracefully"""
        request = self.factory.get('/')
        request.user = self.admin_user
        
        class MockView:
            def __init__(self):
                self.organization = None
        
        view = MockView()
        
        # All permissions should return False when organization is None
        assert IsOrgAdmin().has_permission(request, view) is False
        assert IsOrgEditor().has_permission(request, view) is False
        assert IsOrgMember().has_permission(request, view) is False


class TestObjectPermissions(TestCase):
    """Test object-level permissions"""
    
    def setUp(self):
        """Set up test environment"""
        self.factory = APIRequestFactory()
        
        # Create test users and organization
        self.user = UserFactory()
        self.organization = OrganizationFactory(created_by=self.user)
        
        # Create users with different roles
        self.admin_user = UserFactory()
        self.editor_user = UserFactory()
        self.viewer_user = UserFactory()
        self.non_member_user = UserFactory()
        
        # Create memberships
        AdminMembershipFactory(organization=self.organization, user=self.admin_user)
        EditorMembershipFactory(organization=self.organization, user=self.editor_user)
        ViewerMembershipFactory(organization=self.organization, user=self.viewer_user)
        # Add organization creator as admin
        AdminMembershipFactory(organization=self.organization, user=self.user)
    
    def test_organization_object_permissions(self):
        """Test object permissions with Organization objects"""
        # Test admin user
        request = self.factory.get('/')
        request.user = self.admin_user
        
        assert IsOrgAdmin().has_object_permission(request, None, self.organization) is True
        assert IsOrgEditor().has_object_permission(request, None, self.organization) is True
        assert IsOrgMember().has_object_permission(request, None, self.organization) is True
        
        # Test editor user
        request.user = self.editor_user
        
        assert IsOrgAdmin().has_object_permission(request, None, self.organization) is False
        assert IsOrgEditor().has_object_permission(request, None, self.organization) is True
        assert IsOrgMember().has_object_permission(request, None, self.organization) is True
        
        # Test viewer user
        request.user = self.viewer_user
        
        assert IsOrgAdmin().has_object_permission(request, None, self.organization) is False
        assert IsOrgEditor().has_object_permission(request, None, self.organization) is False
        assert IsOrgMember().has_object_permission(request, None, self.organization) is True
        
        # Test non-member user
        request.user = self.non_member_user
        
        assert IsOrgAdmin().has_object_permission(request, None, self.organization) is False
        assert IsOrgEditor().has_object_permission(request, None, self.organization) is False
        assert IsOrgMember().has_object_permission(request, None, self.organization) is False
    
    def test_object_with_organization_attribute(self):
        """Test object permissions with objects that have organization attribute"""
        # Create a mock object with organization attribute
        class MockObject:
            def __init__(self, organization):
                self.organization = organization
        
        obj = MockObject(self.organization)
        
        # Test admin user
        request = self.factory.get('/')
        request.user = self.admin_user
        
        assert IsOrgAdmin().has_object_permission(request, None, obj) is True
        assert IsOrgEditor().has_object_permission(request, None, obj) is True
        assert IsOrgMember().has_object_permission(request, None, obj) is True
    
    def test_object_with_namespace_attribute(self):
        """Test object permissions with objects that have namespace attribute"""
        from .factories import NamespaceFactory
        
        # Create a namespace
        namespace = NamespaceFactory(organization=self.organization, created_by=self.user)
        
        # Create a mock object with namespace attribute
        class MockObject:
            def __init__(self, namespace):
                self.namespace = namespace
        
        obj = MockObject(namespace)
        
        # Test admin user
        request = self.factory.get('/')
        request.user = self.admin_user
        
        assert IsOrgEditor().has_object_permission(request, None, obj) is True
        assert IsOrgMember().has_object_permission(request, None, obj) is True
    
    def test_object_without_organization_or_namespace(self):
        """Test object permissions with objects that don't have organization or namespace"""
        # Create a mock object without organization or namespace
        class MockObject:
            pass
        
        obj = MockObject()
        
        # Test admin user
        request = self.factory.get('/')
        request.user = self.admin_user
        
        assert IsOrgAdmin().has_object_permission(request, None, obj) is False
        assert IsOrgEditor().has_object_permission(request, None, obj) is False
        assert IsOrgMember().has_object_permission(request, None, obj) is False


class TestPermissionEdgeCases(TestCase):
    """Test edge cases and potential issues in permission classes"""
    
    def setUp(self):
        """Set up test environment"""
        self.factory = APIRequestFactory()
        self.user = UserFactory()
        self.organization = OrganizationFactory(created_by=self.user)
        AdminMembershipFactory(organization=self.organization, user=self.user)
    
    def test_permission_with_none_user(self):
        """Test that permissions handle None user gracefully"""
        request = self.factory.get('/')
        request.user = None
        
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        view = MockView(self.organization)
        
        # These should not raise exceptions
        try:
            assert IsOrgAdmin().has_permission(request, view) is False
            assert IsOrgEditor().has_permission(request, view) is False
            assert IsOrgMember().has_permission(request, view) is False
        except Exception as e:
            self.fail(f"Permission classes should handle None user gracefully, but raised: {e}")
    
    def test_permission_with_anonymous_user(self):
        """Test that permissions handle anonymous user gracefully"""
        from django.contrib.auth.models import AnonymousUser
        
        request = self.factory.get('/')
        request.user = AnonymousUser()
        
        class MockView:
            def __init__(self, organization):
                self.organization = organization
        
        view = MockView(self.organization)
        
        # These should not raise exceptions
        try:
            assert IsOrgAdmin().has_permission(request, view) is False
            assert IsOrgEditor().has_permission(request, view) is False
            assert IsOrgMember().has_permission(request, view) is False
        except Exception as e:
            self.fail(f"Permission classes should handle anonymous user gracefully, but raised: {e}")
    
    def test_permission_with_none_organization_in_view(self):
        """Test that permissions handle None organization in view gracefully"""
        request = self.factory.get('/')
        request.user = self.user
        
        class MockView:
            def __init__(self):
                self.organization = None
        
        view = MockView()
        
        # These should not raise exceptions
        try:
            assert IsOrgAdmin().has_permission(request, view) is False
            assert IsOrgEditor().has_permission(request, view) is False
            assert IsOrgMember().has_permission(request, view) is False
        except Exception as e:
            self.fail(f"Permission classes should handle None organization gracefully, but raised: {e}")
    
    def test_permission_with_invalid_organization_in_view(self):
        """Test that permissions handle invalid organization in view gracefully"""
        request = self.factory.get('/')
        request.user = self.user
        
        class MockView:
            def __init__(self):
                self.organization = "invalid_organization"  # Not an Organization instance
        
        view = MockView()
        
        # These should not raise exceptions
        try:
            assert IsOrgAdmin().has_permission(request, view) is False
            assert IsOrgEditor().has_permission(request, view) is False
            assert IsOrgMember().has_permission(request, view) is False
        except Exception as e:
            self.fail(f"Permission classes should handle invalid organization gracefully, but raised: {e}")
    
    def test_object_permission_with_none_user(self):
        """Test that object permissions handle None user gracefully"""
        request = self.factory.get('/')
        request.user = None
        
        # These should not raise exceptions
        try:
            assert IsOrgAdmin().has_object_permission(request, None, self.organization) is False
            assert IsOrgEditor().has_object_permission(request, None, self.organization) is False
            assert IsOrgMember().has_object_permission(request, None, self.organization) is False
        except Exception as e:
            self.fail(f"Object permission classes should handle None user gracefully, but raised: {e}")
    
    def test_object_permission_with_anonymous_user(self):
        """Test that object permissions handle anonymous user gracefully"""
        from django.contrib.auth.models import AnonymousUser
        
        request = self.factory.get('/')
        request.user = AnonymousUser()
        
        # These should not raise exceptions
        try:
            assert IsOrgAdmin().has_object_permission(request, None, self.organization) is False
            assert IsOrgEditor().has_object_permission(request, None, self.organization) is False
            assert IsOrgMember().has_object_permission(request, None, self.organization) is False
        except Exception as e:
            self.fail(f"Object permission classes should handle anonymous user gracefully, but raised: {e}")
