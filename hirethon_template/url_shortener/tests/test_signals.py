import pytest
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.test import TestCase
from unittest.mock import patch

from hirethon_template.url_shortener.models import Organization, OrganizationMembership
from hirethon_template.url_shortener.signals import create_default_organization
from hirethon_template.users.tests.factories import UserFactory

User = get_user_model()


class TestUserSignals(TestCase):
    """Test signal handlers for user creation"""
    
    def setUp(self):
        """Set up test environment"""
        # Disconnect the signal temporarily to test it manually
        post_save.disconnect(create_default_organization, sender=User)
    
    def tearDown(self):
        """Clean up after tests"""
        # Reconnect the signal
        post_save.connect(create_default_organization, sender=User)
    
    def test_create_organization_for_user_signal(self):
        """Test that organization is created when user is created"""
        # Create a user
        user = UserFactory()
        
        # Manually trigger the signal
        create_default_organization(sender=User, instance=user, created=True)
        
        # Check that organization was created
        assert Organization.objects.filter(created_by=user).exists()
        
        organization = Organization.objects.get(created_by=user)
        assert organization.name == f"{user.name}'s Organization"
        assert organization.created_by == user
    
    def test_create_organization_for_user_existing_user(self):
        """Test that signal doesn't create organization for existing user"""
        # Create a user first
        user = UserFactory()
        
        # Manually trigger the signal with created=False (existing user)
        create_default_organization(sender=User, instance=user, created=False)
        
        # Check that no organization was created
        assert not Organization.objects.filter(created_by=user).exists()
    
    def test_organization_creation_with_membership(self):
        """Test that organization creation also creates admin membership"""
        # Create a user
        user = UserFactory()
        
        # Manually trigger the signal
        create_default_organization(sender=User, instance=user, created=True)
        
        # Check that organization was created
        organization = Organization.objects.get(created_by=user)
        
        # Check that admin membership was created
        assert OrganizationMembership.objects.filter(
            organization=organization,
            user=user,
            role=OrganizationMembership.Role.ADMIN
        ).exists()
        
        membership = OrganizationMembership.objects.get(
            organization=organization,
            user=user
        )
        assert membership.role == OrganizationMembership.Role.ADMIN
        assert membership.invited_by == user  # Creator is set as invited_by in the signal
    
    def test_organization_name_generation(self):
        """Test organization name generation for different user names"""
        # Test with user that has name
        user_with_name = UserFactory(name="John Doe")
        create_default_organization(sender=User, instance=user_with_name, created=True)
        
        organization = Organization.objects.get(created_by=user_with_name)
        assert organization.name == "John Doe's Organization"
        
        # Test with user that has no name (uses email prefix)
        user_without_name = UserFactory(name="", email="jane@example.com")
        create_default_organization(sender=User, instance=user_without_name, created=True)
        
        organization = Organization.objects.get(created_by=user_without_name)
        assert organization.name == "jane's Organization"  # Uses email prefix before @
    
    def test_signal_integration(self):
        """Test that signal works in real user creation flow"""
        # Reconnect the signal for integration test
        post_save.connect(create_default_organization, sender=User)
        
        # Create a user through the normal flow
        user = UserFactory()
        
        # Check that organization was automatically created
        assert Organization.objects.filter(created_by=user).exists()
        
        organization = Organization.objects.get(created_by=user)
        assert organization.created_by == user
        
        # Check that admin membership was created
        assert OrganizationMembership.objects.filter(
            organization=organization,
            user=user,
            role=OrganizationMembership.Role.ADMIN
        ).exists()
    
    def test_multiple_users_organization_creation(self):
        """Test that each user gets their own organization"""
        # Create multiple users
        user1 = UserFactory()
        user2 = UserFactory()
        
        # Trigger signal for both users
        create_default_organization(sender=User, instance=user1, created=True)
        create_default_organization(sender=User, instance=user2, created=True)
        
        # Check that each user has their own organization
        assert Organization.objects.filter(created_by=user1).count() == 1
        assert Organization.objects.filter(created_by=user2).count() == 1
        
        org1 = Organization.objects.get(created_by=user1)
        org2 = Organization.objects.get(created_by=user2)
        
        assert org1 != org2
        assert org1.created_by == user1
        assert org2.created_by == user2
    
    def test_organization_creation_with_existing_organization(self):
        """Test that signal creates organization even if one exists (current behavior)"""
        # Create a user
        user = UserFactory()
        
        # Manually create an organization for the user
        existing_org = Organization.objects.create(
            name="Existing Organization",
            created_by=user
        )
        
        # Trigger the signal
        create_default_organization(sender=User, instance=user, created=True)
        
        # Check that a new organization was created (current signal behavior)
        assert Organization.objects.filter(created_by=user).count() == 2
    
    def test_organization_creation_with_membership_already_exists(self):
        """Test that signal creates new organization and membership even if one exists (current behavior)"""
        # Create a user
        user = UserFactory()
        
        # Manually create an organization and membership
        organization = Organization.objects.create(
            name="Test Organization",
            created_by=user
        )
        OrganizationMembership.objects.create(
            organization=organization,
            user=user,
            role=OrganizationMembership.Role.ADMIN
        )
        
        # Trigger the signal
        create_default_organization(sender=User, instance=user, created=True)
        
        # Check that a new organization and membership were created (current signal behavior)
        assert Organization.objects.filter(created_by=user).count() == 2
        assert OrganizationMembership.objects.filter(user=user).count() == 2
