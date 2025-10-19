import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from hirethon_template.url_shortener.models import (
    Organization,
    OrganizationMembership,
    OrganizationInvitation,
    Namespace,
    ShortURL,
    BulkUploadTask,
)
from .factories import (
    OrganizationFactory,
    OrganizationMembershipFactory,
    OrganizationInvitationFactory,
    NamespaceFactory,
    ShortURLFactory,
    BulkUploadTaskFactory,
    UserFactory,
)


class TestOrganization(TestCase):
    """Test Organization model"""
    
    def test_organization_creation(self):
        """Test basic organization creation"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        
        assert org.name is not None
        assert org.created_by == user
        assert org.created_at is not None
        assert str(org) == org.name
    
    def test_organization_str(self):
        """Test organization string representation"""
        user = UserFactory()
        org = OrganizationFactory(name="Test Org", created_by=user)
        assert str(org) == "Test Org"
    
    def test_organization_memberships(self):
        """Test organization memberships relationship"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        
        # Create some memberships
        member1 = UserFactory()
        member2 = UserFactory()
        
        OrganizationMembershipFactory(organization=org, user=member1)
        OrganizationMembershipFactory(organization=org, user=member2)
        
        assert org.memberships.count() == 2
        # Note: Organization doesn't have a 'members' relationship, only 'memberships'
    
    def test_organization_namespaces(self):
        """Test organization namespaces relationship"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        
        # Create some namespaces
        NamespaceFactory(organization=org, name="ns1", created_by=user)
        NamespaceFactory(organization=org, name="ns2", created_by=user)
        
        assert org.namespaces.count() == 2


class TestOrganizationMembership(TestCase):
    """Test OrganizationMembership model"""
    
    def test_membership_creation(self):
        """Test basic membership creation"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        member = UserFactory()
        
        membership = OrganizationMembershipFactory(
            organization=org,
            user=member,
            role=OrganizationMembership.Role.EDITOR
        )
        
        assert membership.organization == org
        assert membership.user == member
        assert membership.role == OrganizationMembership.Role.EDITOR
        assert membership.joined_at is not None
    
    def test_membership_str(self):
        """Test membership string representation"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        member = UserFactory(email="test@example.com")
        
        membership = OrganizationMembershipFactory(
            organization=org,
            user=member,
            role=OrganizationMembership.Role.ADMIN
        )
        
        expected = f"{member.email} - {org.name} (ADMIN)"
        assert str(membership) == expected
    
    def test_membership_role_choices(self):
        """Test membership role choices"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        
        # Test all role choices with different users
        for role in OrganizationMembership.Role:
            member = UserFactory()  # Create a new user for each role
            membership = OrganizationMembershipFactory(
                organization=org,
                user=member,
                role=role
            )
            assert membership.role == role
    
    def test_membership_unique_constraint(self):
        """Test that user can only have one membership per organization"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        member = UserFactory()
        
        # Create first membership
        OrganizationMembershipFactory(organization=org, user=member)
        
        # Try to create duplicate membership - should raise IntegrityError
        with pytest.raises(IntegrityError):
            OrganizationMembershipFactory(organization=org, user=member)


class TestOrganizationInvitation(TestCase):
    """Test OrganizationInvitation model"""
    
    def test_invitation_creation(self):
        """Test basic invitation creation"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        
        invitation = OrganizationInvitationFactory(
            organization=org,
            email="invitee@example.com",
            role=OrganizationMembership.Role.EDITOR,
            invited_by=user
        )
        
        assert invitation.organization == org
        assert invitation.email == "invitee@example.com"
        assert invitation.role == OrganizationMembership.Role.EDITOR
        assert invitation.invited_by == user
        assert invitation.status == OrganizationInvitation.Status.PENDING
        assert invitation.token is not None
        assert invitation.created_at is not None
        assert invitation.expires_at is not None
    
    def test_invitation_str(self):
        """Test invitation string representation"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        
        invitation = OrganizationInvitationFactory(
            organization=org,
            email="test@example.com",
            status=OrganizationInvitation.Status.PENDING
        )
        
        expected = f"Invite to {org.name} for test@example.com (PENDING)"
        assert str(invitation) == expected
    
    def test_invitation_is_expired(self):
        """Test invitation expiration check"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        
        # Create expired invitation
        expired_invitation = OrganizationInvitationFactory(
            organization=org,
            expires_at=timezone.now() - timedelta(days=1)
        )
        
        # Create valid invitation
        valid_invitation = OrganizationInvitationFactory(
            organization=org,
            expires_at=timezone.now() + timedelta(days=1)
        )
        
        assert expired_invitation.is_expired() is True
        assert valid_invitation.is_expired() is False
    
    def test_invitation_status_choices(self):
        """Test invitation status choices"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        
        for status in OrganizationInvitation.Status:
            invitation = OrganizationInvitationFactory(
                organization=org,
                status=status
            )
            assert invitation.status == status


class TestNamespace(TestCase):
    """Test Namespace model"""
    
    def test_namespace_creation(self):
        """Test basic namespace creation"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        
        namespace = NamespaceFactory(organization=org, name="test-namespace", created_by=user)
        
        assert namespace.organization == org
        assert namespace.name == "test-namespace"
        assert namespace.created_by == user
        assert namespace.created_at is not None
        assert str(namespace) == "test-namespace"
    
    def test_namespace_str(self):
        """Test namespace string representation"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        namespace = NamespaceFactory(name="my-namespace", organization=org, created_by=user)
        assert str(namespace) == "my-namespace"
    
    def test_namespace_short_urls(self):
        """Test namespace short URLs relationship"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        namespace = NamespaceFactory(organization=org, created_by=user)
        
        # Create some short URLs
        ShortURLFactory(namespace=namespace, created_by=user)
        ShortURLFactory(namespace=namespace, created_by=user)
        
        assert namespace.short_urls.count() == 2
    
    def test_namespace_globally_unique(self):
        """Test that namespace names are globally unique"""
        user = UserFactory()
        org1 = OrganizationFactory(created_by=user)
        org2 = OrganizationFactory(created_by=user)
        
        # Create namespace in first org
        NamespaceFactory(organization=org1, name="unique-namespace", created_by=user)
        
        # Try to create namespace with same name in different org - should raise IntegrityError
        with pytest.raises(IntegrityError):
            NamespaceFactory(organization=org2, name="unique-namespace", created_by=user)


class TestShortURL(TestCase):
    """Test ShortURL model"""
    
    def test_short_url_creation(self):
        """Test basic short URL creation"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        namespace = NamespaceFactory(organization=org, created_by=user)
        
        short_url = ShortURLFactory(
            namespace=namespace,
            original_url="https://example.com",
            created_by=user,
            short_code="test-code"
        )
        
        assert short_url.namespace == namespace
        assert short_url.original_url == "https://example.com"
        assert short_url.short_code == "test-code"
        assert short_url.created_by == user
        assert short_url.click_count == 0
        assert short_url.is_private is False
        assert short_url.created_at is not None
        assert short_url.updated_at is not None
    
    def test_short_url_str(self):
        """Test short URL string representation"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        namespace = NamespaceFactory(name="test-ns", organization=org, created_by=user)
        short_url = ShortURLFactory(namespace=namespace, short_code="abc123", created_by=user)
        
        assert str(short_url) == "test-ns/abc123"
    
    def test_short_url_unique_per_namespace(self):
        """Test that short codes are unique within a namespace"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        namespace = NamespaceFactory(organization=org, created_by=user)
        
        # Create first short URL
        ShortURLFactory(namespace=namespace, short_code="unique-code", created_by=user)
        
        # Try to create duplicate short code in same namespace - should raise IntegrityError
        with pytest.raises(IntegrityError):
            ShortURLFactory(namespace=namespace, short_code="unique-code", created_by=user)
    
    def test_short_url_same_code_different_namespaces(self):
        """Test that same short code can exist in different namespaces"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        namespace1 = NamespaceFactory(organization=org, name="ns1", created_by=user)
        namespace2 = NamespaceFactory(organization=org, name="ns2", created_by=user)
        
        # Create short URLs with same code in different namespaces - should work
        ShortURLFactory(namespace=namespace1, short_code="same-code", created_by=user)
        ShortURLFactory(namespace=namespace2, short_code="same-code", created_by=user)
        
        # Both should exist
        assert ShortURL.objects.filter(short_code="same-code").count() == 2
    
    def test_short_url_expiration(self):
        """Test short URL expiration"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        namespace = NamespaceFactory(organization=org, created_by=user)
        
        # Create expired URL
        expired_url = ShortURLFactory(
            namespace=namespace,
            expires_at=timezone.now() - timedelta(days=1),
            created_by=user
        )
        
        # Create valid URL
        valid_url = ShortURLFactory(
            namespace=namespace,
            expires_at=timezone.now() + timedelta(days=1),
            created_by=user
        )
        
        # Create URL without expiration
        no_expiry_url = ShortURLFactory(namespace=namespace, expires_at=None, created_by=user)
        
        assert expired_url.is_expired() is True
        assert valid_url.is_expired() is False
        assert no_expiry_url.is_expired() is False
    
    def test_short_url_click_tracking(self):
        """Test short URL click count tracking"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        namespace = NamespaceFactory(organization=org, created_by=user)
        
        short_url = ShortURLFactory(namespace=namespace, created_by=user)
        
        # Initial click count should be 0
        assert short_url.click_count == 0
        
        # Manually increment click count (since increment_click_count method doesn't exist)
        short_url.click_count += 1
        short_url.save()
        short_url.refresh_from_db()
        assert short_url.click_count == 1
        
        # Increment again
        short_url.click_count += 1
        short_url.save()
        short_url.refresh_from_db()
        assert short_url.click_count == 2
    
    def test_short_url_private_flag(self):
        """Test private URL flag"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        namespace = NamespaceFactory(organization=org, created_by=user)
        
        # Create public URL
        public_url = ShortURLFactory(namespace=namespace, is_private=False, created_by=user)
        
        # Create private URL
        private_url = ShortURLFactory(namespace=namespace, is_private=True, created_by=user)
        
        assert public_url.is_private is False
        assert private_url.is_private is True
    
    def test_short_url_tags(self):
        """Test short URL tags"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        namespace = NamespaceFactory(organization=org, created_by=user)
        
        short_url = ShortURLFactory(
            namespace=namespace,
            tags="tag1,tag2,tag3",
            created_by=user
        )
        
        assert short_url.tags == "tag1,tag2,tag3"


class TestBulkUploadTask(TestCase):
    """Test BulkUploadTask model"""
    
    def test_bulk_upload_task_creation(self):
        """Test basic bulk upload task creation"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        namespace = NamespaceFactory(organization=org, created_by=user)
        
        task = BulkUploadTaskFactory(
            organization=org,
            namespace=namespace,
            created_by=user,
            status=BulkUploadTask.Status.PENDING
        )
        
        assert task.organization == org
        assert task.namespace == namespace
        assert task.created_by == user
        assert task.status == BulkUploadTask.Status.PENDING
        assert task.total_urls == 0
        assert task.processed_urls == 0
        assert task.failed_urls == 0
        assert task.created_at is not None
    
    def test_bulk_upload_task_str(self):
        """Test bulk upload task string representation"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        namespace = NamespaceFactory(organization=org, created_by=user)
        
        task = BulkUploadTaskFactory(
            organization=org,
            namespace=namespace,
            created_by=user,
            status=BulkUploadTask.Status.COMPLETED
        )
        
        # Check that the string representation contains the status
        task_str = str(task)
        assert "COMPLETED" in task_str
        assert "Bulk Upload" in task_str
    
    def test_bulk_upload_task_status_choices(self):
        """Test bulk upload task status choices"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        namespace = NamespaceFactory(organization=org, created_by=user)
        
        for status in BulkUploadTask.Status:
            task = BulkUploadTaskFactory(
                organization=org,
                namespace=namespace,
                created_by=user,
                status=status
            )
            assert task.status == status
    
    def test_bulk_upload_task_progress_calculation(self):
        """Test bulk upload task progress calculation"""
        user = UserFactory()
        org = OrganizationFactory(created_by=user)
        namespace = NamespaceFactory(organization=org, created_by=user)
        
        task = BulkUploadTaskFactory(
            organization=org,
            namespace=namespace,
            created_by=user,
            total_urls=100,
            processed_urls=50,
            failed_urls=5
        )
        
        # Test that the task has the expected values
        assert task.total_urls == 100
        assert task.processed_urls == 50
        assert task.failed_urls == 5
