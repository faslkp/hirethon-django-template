import secrets
from datetime import datetime, timedelta
from typing import Any, Sequence

from django.contrib.auth import get_user_model
from django.utils import timezone
from factory import Faker, LazyAttribute, post_generation, Sequence as FactorySequence
from factory.django import DjangoModelFactory

from hirethon_template.url_shortener.models import (
    BulkUploadTask,
    Namespace,
    Organization,
    OrganizationInvitation,
    OrganizationMembership,
    ShortURL,
)
from hirethon_template.users.tests.factories import UserFactory

User = get_user_model()


class OrganizationFactory(DjangoModelFactory):
    """Factory for creating test organizations"""
    
    name = Faker("company")
    created_by = None  # Will be set in tests
    
    class Meta:
        model = Organization
        django_get_or_create = ["name"]


class OrganizationMembershipFactory(DjangoModelFactory):
    """Factory for creating organization memberships"""
    
    organization = None  # Will be set in tests
    user = None  # Will be set in tests
    role = OrganizationMembership.Role.VIEWER
    invited_by = None
    
    class Meta:
        model = OrganizationMembership


class OrganizationInvitationFactory(DjangoModelFactory):
    """Factory for creating organization invitations"""
    
    organization = None  # Will be set in tests
    email = Faker("email")
    role = OrganizationMembership.Role.VIEWER
    token = LazyAttribute(lambda obj: secrets.token_urlsafe(32))
    status = OrganizationInvitation.Status.PENDING
    invited_by = None
    created_at = LazyAttribute(lambda obj: timezone.now())
    expires_at = LazyAttribute(lambda obj: timezone.now() + timedelta(days=7))
    
    class Meta:
        model = OrganizationInvitation


class NamespaceFactory(DjangoModelFactory):
    """Factory for creating namespaces with unique names"""
    
    name = FactorySequence(lambda n: f"test-namespace-{n}")
    organization = None  # Will be set in tests
    created_by = None  # Will be set in tests
    
    class Meta:
        model = Namespace


class ShortURLFactory(DjangoModelFactory):
    """Factory for creating short URLs"""
    
    namespace = None  # Will be set in tests
    short_code = LazyAttribute(lambda obj: secrets.token_urlsafe(8))
    original_url = Faker("url")
    created_by = None  # Will be set in tests
    click_count = 0
    is_private = False
    tags = ""
    expires_at = None
    
    class Meta:
        model = ShortURL


class BulkUploadTaskFactory(DjangoModelFactory):
    """Factory for creating bulk upload tasks"""
    
    organization = None  # Will be set in tests
    namespace = None  # Will be set in tests
    created_by = None  # Will be set in tests
    status = BulkUploadTask.Status.PENDING
    input_file = None
    output_file = None
    error_log = ""
    total_urls = 0
    processed_urls = 0
    failed_urls = 0
    
    class Meta:
        model = BulkUploadTask


# Specialized factories for common test scenarios

class AdminMembershipFactory(OrganizationMembershipFactory):
    """Factory for creating admin memberships"""
    role = OrganizationMembership.Role.ADMIN


class EditorMembershipFactory(OrganizationMembershipFactory):
    """Factory for creating editor memberships"""
    role = OrganizationMembership.Role.EDITOR


class ViewerMembershipFactory(OrganizationMembershipFactory):
    """Factory for creating viewer memberships"""
    role = OrganizationMembership.Role.VIEWER


class PrivateShortURLFactory(ShortURLFactory):
    """Factory for creating private short URLs"""
    is_private = True


class ExpiredShortURLFactory(ShortURLFactory):
    """Factory for creating expired short URLs"""
    expires_at = LazyAttribute(lambda obj: timezone.now() - timedelta(days=1))


class ExpiringShortURLFactory(ShortURLFactory):
    """Factory for creating short URLs that expire soon"""
    expires_at = LazyAttribute(lambda obj: timezone.now() + timedelta(hours=1))


class CompletedBulkUploadTaskFactory(BulkUploadTaskFactory):
    """Factory for creating completed bulk upload tasks"""
    status = BulkUploadTask.Status.COMPLETED
    total_urls = 10
    processed_urls = 10
    successful_urls = 8
    failed_urls = 2


class FailedBulkUploadTaskFactory(BulkUploadTaskFactory):
    """Factory for creating failed bulk upload tasks"""
    status = BulkUploadTask.Status.FAILED
    error_message = "Processing failed due to invalid data"
