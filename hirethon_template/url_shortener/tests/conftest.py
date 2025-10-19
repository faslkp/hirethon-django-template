import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from hirethon_template.users.tests.factories import UserFactory
from .factories import (
    AdminMembershipFactory,
    BulkUploadTaskFactory,
    EditorMembershipFactory,
    NamespaceFactory,
    OrganizationFactory,
    OrganizationInvitationFactory,
    ShortURLFactory,
    ViewerMembershipFactory,
)

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user"""
    return UserFactory()


@pytest.fixture
def organization(db, user):
    """Create a test organization with the user as creator"""
    org = OrganizationFactory(created_by=user)
    # Add the creator as an admin member (like the API does)
    AdminMembershipFactory(organization=org, user=user)
    return org


@pytest.fixture
def namespace(db, organization, user):
    """Create a test namespace"""
    return NamespaceFactory(organization=organization, created_by=user)


@pytest.fixture
def short_url(db, namespace, user):
    """Create a test short URL"""
    return ShortURLFactory(namespace=namespace, created_by=user)


@pytest.fixture
def admin_user(db, organization):
    """Create a user with ADMIN role in the organization"""
    user = UserFactory()
    AdminMembershipFactory(organization=organization, user=user)
    return user


@pytest.fixture
def editor_user(db, organization):
    """Create a user with EDITOR role in the organization"""
    user = UserFactory()
    EditorMembershipFactory(organization=organization, user=user)
    return user


@pytest.fixture
def viewer_user(db, organization):
    """Create a user with VIEWER role in the organization"""
    user = UserFactory()
    ViewerMembershipFactory(organization=organization, user=user)
    return user


@pytest.fixture
def non_member_user(db):
    """Create a user who is not a member of any organization"""
    return UserFactory()


@pytest.fixture
def organization_with_members(db, organization):
    """Create an organization with multiple members of different roles"""
    admin = UserFactory()
    editor = UserFactory()
    viewer = UserFactory()
    
    AdminMembershipFactory(organization=organization, user=admin)
    EditorMembershipFactory(organization=organization, user=editor)
    ViewerMembershipFactory(organization=organization, user=viewer)
    
    return {
        'organization': organization,
        'admin': admin,
        'editor': editor,
        'viewer': viewer,
    }


@pytest.fixture
def invitation(db, organization, user):
    """Create a test invitation"""
    return OrganizationInvitationFactory(
        organization=organization,
        invited_by=user
    )


@pytest.fixture
def bulk_upload_task(db, organization, namespace, user):
    """Create a test bulk upload task"""
    return BulkUploadTaskFactory(
        organization=organization,
        namespace=namespace,
        created_by=user
    )


@pytest.fixture
def request_factory():
    """Django RequestFactory for creating test requests"""
    return RequestFactory()


@pytest.fixture
def api_client():
    """DRF API client for testing API endpoints"""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_api_client(api_client, user):
    """API client with authenticated user"""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_api_client(api_client, organization):
    """API client with organization creator as admin"""
    api_client.force_authenticate(user=organization.created_by)
    return api_client


@pytest.fixture
def editor_api_client(api_client, editor_user):
    """API client with editor user"""
    api_client.force_authenticate(user=editor_user)
    return api_client


@pytest.fixture
def viewer_api_client(api_client, viewer_user):
    """API client with viewer user"""
    api_client.force_authenticate(user=viewer_user)
    return api_client


@pytest.fixture
def multiple_organizations(db, user):
    """Create multiple organizations for testing"""
    org1 = OrganizationFactory(created_by=user, name="Organization 1")
    org2 = OrganizationFactory(created_by=user, name="Organization 2")
    
    # Add some members to each organization
    user1 = UserFactory()
    user2 = UserFactory()
    
    AdminMembershipFactory(organization=org1, user=user1)
    EditorMembershipFactory(organization=org2, user=user2)
    
    return {
        'org1': org1,
        'org2': org2,
        'user1': user1,
        'user2': user2,
    }


@pytest.fixture
def namespace_with_urls(db, namespace, user):
    """Create a namespace with multiple short URLs"""
    urls = []
    for i in range(5):
        url = ShortURLFactory(
            namespace=namespace,
            created_by=user,
            short_code=f"test-{i}",
            original_url=f"https://example.com/page{i}"
        )
        urls.append(url)
    
    return {
        'namespace': namespace,
        'urls': urls,
    }


@pytest.fixture
def expired_url(db, namespace, user):
    """Create an expired short URL"""
    from datetime import timedelta
    from django.utils import timezone
    
    return ShortURLFactory(
        namespace=namespace,
        created_by=user,
        expires_at=timezone.now() - timedelta(days=1)
    )


@pytest.fixture
def private_url(db, namespace, user):
    """Create a private short URL"""
    return ShortURLFactory(
        namespace=namespace,
        created_by=user,
        is_private=True
    )


@pytest.fixture
def mock_s3_storage(monkeypatch):
    """Mock S3 storage for testing"""
    from unittest.mock import MagicMock
    
    mock_storage = MagicMock()
    mock_storage.url.return_value = "https://mock-s3-url.com/file.txt"
    mock_storage.save.return_value = "mock-file-path.txt"
    
    monkeypatch.setattr(
        "hirethon_template.url_shortener.models.default_storage",
        mock_storage
    )
    
    return mock_storage


@pytest.fixture
def mock_celery_task(monkeypatch):
    """Mock Celery tasks for testing"""
    from unittest.mock import patch
    
    with patch('hirethon_template.url_shortener.tasks.process_bulk_upload.delay') as mock_task:
        mock_task.return_value.id = "mock-task-id"
        yield mock_task
