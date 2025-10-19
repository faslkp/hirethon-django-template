import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

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
    OrganizationInvitationFactory,
    AdminMembershipFactory,
    EditorMembershipFactory,
    ViewerMembershipFactory,
    NamespaceFactory,
    ShortURLFactory,
    BulkUploadTaskFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestOrganizationViewSet:
    """Test Organization API endpoints"""
    
    def test_list_organizations_authenticated_user(self, admin_api_client, organization):
        """Test that authenticated user can list their organizations"""
        url = reverse('api:organization-list')
        response = admin_api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # The user should be a member of at least the test organization
        org_names = [org['name'] for org in response.data]
        assert organization.name in org_names
    
    def test_list_organizations_unauthenticated(self, api_client):
        """Test that unauthenticated user cannot list organizations"""
        url = reverse('api:organization-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_organizations_multiple_orgs(self, admin_api_client, organization):
        """Test listing multiple organizations"""
        # Create multiple organizations with memberships
        org1 = OrganizationFactory(created_by=organization.created_by, name="Org 1")
        org2 = OrganizationFactory(created_by=organization.created_by, name="Org 2")
        
        # Add user as admin to both organizations
        AdminMembershipFactory(organization=org1, user=organization.created_by)
        AdminMembershipFactory(organization=org2, user=organization.created_by)
        
        url = reverse('api:organization-list')
        response = admin_api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # The user should be a member of at least the test organizations
        org_names = [org['name'] for org in response.data]
        assert "Org 1" in org_names
        assert "Org 2" in org_names
    
    def test_create_organization(self, authenticated_api_client, user):
        """Test creating a new organization"""
        url = reverse('api:organization-list')
        data = {
            'name': 'New Organization'
        }
        
        response = authenticated_api_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Organization'
        assert response.data['created_by']['id'] == user.id
        
        # Check that organization was created in database
        assert Organization.objects.filter(name='New Organization').exists()
    
    def test_create_organization_validation(self, authenticated_api_client):
        """Test organization creation validation"""
        url = reverse('api:organization-list')
        data = {
            'name': ''  # Empty name should fail
        }
        
        response = authenticated_api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
    
    def test_retrieve_organization(self, admin_api_client, organization):
        """Test retrieving a specific organization"""
        url = reverse('api:organization-detail', kwargs={'pk': organization.pk})
        response = admin_api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == organization.name
        assert response.data['id'] == organization.id
    
    def test_retrieve_organization_not_found(self, authenticated_api_client):
        """Test retrieving non-existent organization"""
        url = reverse('api:organization-detail', kwargs={'pk': 99999})
        response = authenticated_api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_organization(self, admin_api_client, organization):
        """Test updating an organization"""
        url = reverse('api:organization-detail', kwargs={'pk': organization.pk})
        data = {
            'name': 'Updated Organization'
        }
        
        response = admin_api_client.put(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Organization'
        
        # Check that organization was updated in database
        organization.refresh_from_db()
        assert organization.name == 'Updated Organization'
    
    def test_partial_update_organization(self, admin_api_client, organization):
        """Test partial update of an organization"""
        url = reverse('api:organization-detail', kwargs={'pk': organization.pk})
        data = {'name': 'Partially Updated'}
        
        response = admin_api_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Partially Updated'
        
        # Check that only name was updated
        organization.refresh_from_db()
        assert organization.name == 'Partially Updated'
    
    def test_delete_organization(self, admin_api_client, organization):
        """Test deleting an organization"""
        url = reverse('api:organization-detail', kwargs={'pk': organization.pk})
        response = admin_api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Check that organization was deleted
        assert not Organization.objects.filter(pk=organization.pk).exists()
    
    def test_invite_member(self, admin_api_client, organization):
        """Test inviting a member to organization"""
        url = reverse('api:organization-invite', kwargs={'pk': organization.pk})
        data = {
            'email': 'newmember@example.com',
            'role': 'EDITOR'
        }
        
        response = admin_api_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == 'newmember@example.com'
        assert response.data['role'] == 'EDITOR'
        
        # Check that invitation was created
        assert OrganizationInvitation.objects.filter(
            organization=organization,
            email='newmember@example.com'
        ).exists()
    
    def test_invite_member_non_admin(self, editor_api_client, organization):
        """Test that non-admin cannot invite members"""
        url = reverse('api:organization-invite', kwargs={'pk': organization.pk})
        data = {
            'email': 'newmember@example.com',
            'role': 'EDITOR'
        }
        
        response = editor_api_client.post(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_invite_member_duplicate_email(self, admin_api_client, organization):
        """Test inviting member with duplicate email"""
        # Create existing invitation
        OrganizationInvitationFactory(
            organization=organization,
            email='existing@example.com'
        )
        
        url = reverse('api:organization-invite', kwargs={'pk': organization.pk})
        data = {
            'email': 'existing@example.com',
            'role': 'EDITOR'
        }
        
        response = admin_api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data
    
    def test_list_members(self, authenticated_api_client, organization_with_members):
        """Test listing organization members"""
        organization = organization_with_members['organization']
        url = reverse('api:organization-members', kwargs={'pk': organization.pk})
        
        response = authenticated_api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3  # admin, editor, viewer
        
        # Check that all members are included
        member_emails = [member['user']['email'] for member in response.data]
        assert organization_with_members['admin'].email in member_emails
        assert organization_with_members['editor'].email in member_emails
        assert organization_with_members['viewer'].email in member_emails
    
    def test_remove_member(self, admin_api_client, organization_with_members):
        """Test removing a member from organization"""
        organization = organization_with_members['organization']
        member_to_remove = organization_with_members['viewer']
        
        url = reverse('api:organization-remove-member', kwargs={
            'pk': organization.pk
        })
        
        response = admin_api_client.delete(url, {'user_id': member_to_remove.pk})
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Check that membership was removed
        assert not OrganizationMembership.objects.filter(
            organization=organization,
            user=member_to_remove
        ).exists()
    
    def test_remove_member_non_admin(self, editor_api_client, organization_with_members):
        """Test that non-admin cannot remove members"""
        organization = organization_with_members['organization']
        member_to_remove = organization_with_members['viewer']
        
        url = reverse('api:organization-remove-member', kwargs={
            'pk': organization.pk
        })
        
        response = editor_api_client.delete(url, {'user_id': member_to_remove.pk})
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_list_invitations(self, admin_api_client, organization):
        """Test listing organization invitations"""
        # Create some invitations
        OrganizationInvitationFactory(organization=organization)
        OrganizationInvitationFactory(organization=organization)
        
        url = reverse('api:organization-invitations', kwargs={'pk': organization.pk})
        response = admin_api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
    
    def test_cancel_invitation(self, admin_api_client, invitation):
        """Test canceling an invitation"""
        url = reverse('api:organization-cancel-invitation', kwargs={
            'pk': invitation.organization.pk
        })
        
        response = admin_api_client.post(url, {'invitation_id': invitation.pk})
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Check that invitation was canceled
        invitation.refresh_from_db()
        assert invitation.status == OrganizationInvitation.Status.CANCELED


@pytest.mark.django_db
class TestNamespaceViewSet:
    """Test Namespace API endpoints"""
    
    def test_list_namespaces(self, authenticated_api_client, namespace):
        """Test listing namespaces"""
        url = reverse('api:namespace-list')
        response = authenticated_api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == namespace.name
    
    def test_create_namespace(self, admin_api_client, organization):
        """Test creating a namespace"""
        url = reverse('api:namespace-list')
        data = {
            'name': 'new-namespace',
            'organization_id': organization.pk
        }
        
        response = admin_api_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'new-namespace'
        
        # Check that namespace was created
        assert Namespace.objects.filter(name='new-namespace').exists()
    
    def test_create_namespace_non_admin(self, editor_api_client, organization):
        """Test that non-admin cannot create namespaces"""
        url = reverse('api:namespace-list')
        data = {
            'name': 'new-namespace',
            'organization_id': organization.pk
        }
        
        response = editor_api_client.post(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_namespace_duplicate_name(self, admin_api_client, organization):
        """Test creating namespace with duplicate name"""
        # Create existing namespace
        NamespaceFactory(name='existing-namespace', organization=organization, created_by=organization.created_by)
        
        url = reverse('api:namespace-list')
        data = {
            'name': 'existing-namespace',
            'organization': organization.pk
        }
        
        response = admin_api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
    
    def test_delete_namespace(self, admin_api_client, namespace):
        """Test deleting a namespace"""
        url = reverse('api:namespace-detail', kwargs={'pk': namespace.pk})
        response = admin_api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Check that namespace was deleted
        assert not Namespace.objects.filter(pk=namespace.pk).exists()
    
    def test_delete_namespace_non_admin(self, editor_api_client, namespace):
        """Test that non-admin cannot delete namespaces"""
        url = reverse('api:namespace-detail', kwargs={'pk': namespace.pk})
        response = editor_api_client.delete(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestShortURLViewSet:
    """Test ShortURL API endpoints"""
    
    def test_list_short_urls(self, authenticated_api_client, short_url):
        """Test listing short URLs"""
        url = reverse('api:short-url-list')
        response = authenticated_api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['short_code'] == short_url.short_code
    
    def test_create_short_url(self, editor_api_client, namespace):
        """Test creating a short URL"""
        url = reverse('api:short-url-list')
        data = {
            'namespace_id': namespace.pk,
            'original_url': 'https://example.com',
            'short_code': 'test-code',
            'is_private': False,
            'tags': 'test,example'
        }
        
        response = editor_api_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['original_url'] == 'https://example.com'
        assert response.data['short_code'] == 'test-code'
        
        # Check that short URL was created
        assert ShortURL.objects.filter(short_code='test-code').exists()
    
    def test_create_short_url_viewer(self, viewer_api_client, namespace):
        """Test that viewer cannot create short URLs"""
        url = reverse('api:short-url-list')
        data = {
            'namespace_id': namespace.pk,
            'original_url': 'https://example.com',
            'short_code': 'test-code'
        }
        
        response = viewer_api_client.post(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_short_url_duplicate_code(self, editor_api_client, namespace, short_url):
        """Test creating short URL with duplicate code in same namespace"""
        url = reverse('api:short-url-list')
        data = {
            'namespace_id': namespace.pk,
            'original_url': 'https://example.com',
            'short_code': short_url.short_code  # Duplicate code
        }
        
        response = editor_api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'short_code' in response.data
    
    def test_retrieve_short_url(self, authenticated_api_client, short_url):
        """Test retrieving a specific short URL"""
        url = reverse('api:short-url-detail', kwargs={'pk': short_url.pk})
        response = authenticated_api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['short_code'] == short_url.short_code
        assert response.data['original_url'] == short_url.original_url
    
    def test_update_short_url(self, editor_api_client, short_url):
        """Test updating a short URL"""
        url = reverse('api:short-url-detail', kwargs={'pk': short_url.pk})
        data = {
            'original_url': 'https://updated-example.com',
            'short_code': short_url.short_code,
            'is_private': True,
            'tags': 'updated,test'
        }
        
        response = editor_api_client.put(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['original_url'] == 'https://updated-example.com'
        assert response.data['is_private'] is True
        
        # Check that short URL was updated
        short_url.refresh_from_db()
        assert short_url.original_url == 'https://updated-example.com'
        assert short_url.is_private is True
    
    def test_delete_short_url(self, editor_api_client, short_url):
        """Test deleting a short URL"""
        url = reverse('api:short-url-detail', kwargs={'pk': short_url.pk})
        response = editor_api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Check that short URL was deleted
        assert not ShortURL.objects.filter(pk=short_url.pk).exists()
    
    def test_generate_qr_code(self, authenticated_api_client, short_url):
        """Test generating QR code for short URL"""
        url = reverse('api:short-url-generate-qr', kwargs={'pk': short_url.pk})
        response = authenticated_api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'qr_code_url' in response.data
        assert response.data['qr_code_url'] is not None


@pytest.mark.django_db
class TestBulkUploadViewSet:
    """Test BulkUpload API endpoints"""
    
    def test_list_bulk_uploads(self, authenticated_api_client, bulk_upload_task):
        """Test listing bulk upload tasks"""
        url = reverse('api:bulk-upload-list')
        response = authenticated_api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['status'] == bulk_upload_task.status
    
    def test_create_bulk_upload(self, admin_api_client, organization, namespace):
        """Test creating a bulk upload task"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        url = reverse('api:bulk-upload-list')
        
        # Create a simple test file
        test_file = SimpleUploadedFile(
            "test_bulk_upload.xlsx",
            b"test file content",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        data = {
            'organization_id': organization.pk,
            'namespace_id': namespace.pk,
            'input_file': test_file
        }
        
        response = admin_api_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['organization']['id'] == organization.pk
        
        # Check that bulk upload task was created
        assert BulkUploadTask.objects.filter(organization=organization).exists()
    
    def test_create_bulk_upload_non_admin(self, editor_api_client, organization, namespace):
        """Test that non-admin cannot create bulk upload tasks"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        url = reverse('api:bulk-upload-list')
        
        # Create a simple test file
        test_file = SimpleUploadedFile(
            "test_bulk_upload.xlsx",
            b"test file content",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        data = {
            'organization_id': organization.pk,
            'namespace_id': namespace.pk,
            'input_file': test_file
        }
        
        response = editor_api_client.post(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_retrieve_bulk_upload(self, authenticated_api_client, bulk_upload_task):
        """Test retrieving a specific bulk upload task"""
        url = reverse('api:bulk-upload-detail', kwargs={'pk': bulk_upload_task.pk})
        response = authenticated_api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == bulk_upload_task.pk
        assert response.data['status'] == bulk_upload_task.status
    
    def test_download_results(self, authenticated_api_client, bulk_upload_task):
        """Test downloading bulk upload results"""
        url = reverse('api:bulk-upload-download', kwargs={'pk': bulk_upload_task.pk})
        response = authenticated_api_client.get(url)
        
        # This would return a file download in real scenario
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
