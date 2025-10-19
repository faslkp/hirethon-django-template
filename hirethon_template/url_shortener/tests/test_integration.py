import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

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
    NamespaceFactory,
    ShortURLFactory,
    BulkUploadTaskFactory,
    UserFactory,
)

User = get_user_model()


class TestUserJourneyIntegration(TestCase):
    """Test complete user journey from signup to URL creation"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        self.api_client = APIClient()
    
    def test_complete_user_journey(self):
        """Test complete user journey: signup → create org → namespace → URL"""
        # Step 1: User signs up
        user_data = {
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'name': 'Test User'
        }
        
        response = self.client.post('/rest-auth/registration/', user_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Get user and tokens
        user = User.objects.get(email='test@example.com')
        access_token = response.data['access']
        
        # Step 2: User is automatically assigned to an organization
        assert Organization.objects.filter(created_by=user).exists()
        organization = Organization.objects.get(created_by=user)
        assert organization.name == "Test User's Organization"
        
        # Step 3: User has admin role in their organization
        assert OrganizationMembership.objects.filter(
            organization=organization,
            user=user,
            role=OrganizationMembership.Role.ADMIN
        ).exists()
        
        # Step 4: User creates a namespace
        self.api_client.force_authenticate(user=user)
        namespace_data = {
            'name': 'my-namespace',
            'organization': organization.id
        }
        
        response = self.api_client.post('/api/namespaces/', namespace_data)
        assert response.status_code == status.HTTP_201_CREATED
        namespace = Namespace.objects.get(name='my-namespace')
        
        # Step 5: User creates a short URL
        url_data = {
            'namespace': namespace.id,
            'original_url': 'https://example.com',
            'short_code': 'test123',
            'is_private': False,
            'tags': 'test,example'
        }
        
        response = self.api_client.post('/api/short-urls/', url_data)
        assert response.status_code == status.HTTP_201_CREATED
        short_url = ShortURL.objects.get(short_code='test123')
        assert short_url.original_url == 'https://example.com'
        assert short_url.namespace == namespace
        assert short_url.created_by == user
        
        # Step 6: User can access the short URL
        response = self.client.get(f'/r/{short_url.short_code}')
        assert response.status_code == 302
        assert response.url == 'https://example.com'
        
        # Step 7: Click count is incremented
        short_url.refresh_from_db()
        assert short_url.click_count == 1


class TestInvitationFlowIntegration(TestCase):
    """Test complete invitation flow"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        self.api_client = APIClient()
        
        # Create admin user and organization
        self.admin = UserFactory()
        self.organization = OrganizationFactory(created_by=self.admin)
        AdminMembershipFactory(organization=self.organization, user=self.admin)
        
        # Create invitee user
        self.invitee = UserFactory()
    
    def test_invitation_flow(self):
        """Test complete invitation flow: invite → accept → access"""
        # Step 1: Admin invites a user
        self.api_client.force_authenticate(user=self.admin)
        invite_data = {
            'email': self.invitee.email,
            'role': 'EDITOR'
        }
        
        response = self.api_client.post(
            f'/api/organizations/{self.organization.id}/invite/',
            invite_data
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Check invitation was created
        invitation = OrganizationInvitation.objects.get(
            organization=self.organization,
            email=self.invitee.email
        )
        assert invitation.role == 'EDITOR'
        assert invitation.status == OrganizationInvitation.Status.PENDING
        
        # Step 2: Invitee accepts invitation
        # Simulate invitation acceptance (in real app, this would be via email link)
        invitation.status = OrganizationInvitation.Status.ACCEPTED
        invitation.save()
        
        # Create membership for invitee
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.invitee,
            role=OrganizationMembership.Role.EDITOR,
            invited_by=self.admin
        )
        
        # Step 3: Invitee can now access organization resources
        self.api_client.force_authenticate(user=self.invitee)
        
        # Create namespace (as editor)
        namespace_data = {
            'name': 'invitee-namespace',
            'organization': self.organization.id
        }
        
        response = self.api_client.post('/api/namespaces/', namespace_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Create short URL (as editor)
        namespace = Namespace.objects.get(name='invitee-namespace')
        url_data = {
            'namespace': namespace.id,
            'original_url': 'https://invitee-example.com',
            'short_code': 'invitee123'
        }
        
        response = self.api_client.post('/api/short-urls/', url_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Step 4: Invitee can access their short URL
        short_url = ShortURL.objects.get(short_code='invitee123')
        response = self.client.get(f'/r/{short_url.short_code}')
        assert response.status_code == 302
        assert response.url == 'https://invitee-example.com'


class TestBulkUploadFlowIntegration(TestCase):
    """Test complete bulk upload flow"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        self.api_client = APIClient()
        
        # Create admin user and organization
        self.admin = UserFactory()
        self.organization = OrganizationFactory(created_by=self.admin)
        AdminMembershipFactory(organization=self.organization, user=self.admin)
        
        # Create namespace
        self.namespace = NamespaceFactory(organization=self.organization)
    
    def test_bulk_upload_flow(self):
        """Test complete bulk upload flow: upload → process → download"""
        # Step 1: Admin creates bulk upload task
        self.api_client.force_authenticate(user=self.admin)
        
        # Mock Excel file upload
        excel_content = b"""original_url,short_code,tags,is_private,expires_at
https://example1.com,bulk1,test,false,2024-12-31
https://example2.com,bulk2,test,true,2024-12-31
https://example3.com,bulk3,test,false,2024-12-31"""
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        excel_file = SimpleUploadedFile(
            "bulk_upload.xlsx",
            excel_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        bulk_data = {
            'organization': self.organization.id,
            'input_file': excel_file
        }
        
        response = self.api_client.post('/api/bulk-uploads/', bulk_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        bulk_task = BulkUploadTask.objects.get(organization=self.organization)
        assert bulk_task.status == BulkUploadTask.Status.PENDING
        
        # Step 2: Process bulk upload (simulate Celery task)
        with patch('hirethon_template.url_shortener.tasks.process_bulk_upload.delay') as mock_task:
            mock_task.return_value.id = 'mock-task-id'
            
            # Simulate task processing
            from hirethon_template.url_shortener.tasks import process_bulk_upload
            result = process_bulk_upload(bulk_task.id)
            
            # Check that URLs were created
            assert ShortURL.objects.filter(short_code='bulk1').exists()
            assert ShortURL.objects.filter(short_code='bulk2').exists()
            assert ShortURL.objects.filter(short_code='bulk3').exists()
            
            # Check that private URL was created correctly
            private_url = ShortURL.objects.get(short_code='bulk2')
            assert private_url.is_private is True
        
        # Step 3: Admin can view task status
        response = self.api_client.get(f'/api/bulk-uploads/{bulk_task.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == BulkUploadTask.Status.COMPLETED
        
        # Step 4: URLs are accessible
        response = self.client.get('/r/bulk1')
        assert response.status_code == 302
        assert response.url == 'https://example1.com'
        
        response = self.client.get('/r/bulk2')
        assert response.status_code == 401  # Private URL requires auth


class TestPrivateURLFlowIntegration(TestCase):
    """Test complete private URL flow"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        self.api_client = APIClient()
        
        # Create user and organization
        self.user = UserFactory()
        self.organization = OrganizationFactory(created_by=self.user)
        AdminMembershipFactory(organization=self.organization, user=self.user)
        
        # Create namespace and private URL
        self.namespace = NamespaceFactory(organization=self.organization)
        self.private_url = ShortURLFactory(
            namespace=self.namespace,
            short_code='private123',
            original_url='https://private-example.com',
            is_private=True,
            created_by=self.user
        )
    
    def test_private_url_flow(self):
        """Test complete private URL flow: create → authenticate → access"""
        # Step 1: User creates private URL (already done in setUp)
        assert self.private_url.is_private is True
        
        # Step 2: Anonymous user cannot access private URL
        response = self.client.get('/r/private123')
        assert response.status_code == 401
        
        # Step 3: Authenticated user can access private URL
        # Mock JWT token validation
        with patch('hirethon_template.url_shortener.views.jwt.decode') as mock_decode:
            mock_decode.return_value = {'user_id': self.user.id}
            
            response = self.client.get(
                '/r/private123',
                HTTP_AUTHORIZATION='Bearer valid-token'
            )
            assert response.status_code == 302
            assert response.url == 'https://private-example.com'
        
        # Step 4: Click count is incremented
        self.private_url.refresh_from_db()
        assert self.private_url.click_count == 1


class TestMultiUserOrganizationIntegration(TestCase):
    """Test multi-user organization functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        self.api_client = APIClient()
        
        # Create organization with multiple users
        self.admin = UserFactory()
        self.organization = OrganizationFactory(created_by=self.admin)
        AdminMembershipFactory(organization=self.organization, user=self.admin)
        
        self.editor = UserFactory()
        EditorMembershipFactory(organization=self.organization, user=self.editor)
        
        self.viewer = UserFactory()
        ViewerMembershipFactory(organization=self.organization, user=self.viewer)
        
        # Create namespace
        self.namespace = NamespaceFactory(organization=self.organization)
    
    def test_multi_user_permissions(self):
        """Test that different users have appropriate permissions"""
        # Admin can create namespace
        self.api_client.force_authenticate(user=self.admin)
        namespace_data = {'name': 'admin-namespace', 'organization': self.organization.id}
        response = self.api_client.post('/api/namespaces/', namespace_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Editor can create short URL
        self.api_client.force_authenticate(user=self.editor)
        url_data = {
            'namespace': self.namespace.id,
            'original_url': 'https://editor-example.com',
            'short_code': 'editor123'
        }
        response = self.api_client.post('/api/short-urls/', url_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Viewer cannot create short URL
        self.api_client.force_authenticate(user=self.viewer)
        url_data = {
            'namespace': self.namespace.id,
            'original_url': 'https://viewer-example.com',
            'short_code': 'viewer123'
        }
        response = self.api_client.post('/api/short-urls/', url_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # But viewer can view short URLs
        response = self.api_client.get('/api/short-urls/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1  # Only the one created by editor
    
    def test_multi_user_collaboration(self):
        """Test collaboration between multiple users"""
        # Editor creates a short URL
        self.api_client.force_authenticate(user=self.editor)
        url_data = {
            'namespace': self.namespace.id,
            'original_url': 'https://collaboration-example.com',
            'short_code': 'collab123'
        }
        response = self.api_client.post('/api/short-urls/', url_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Admin can update the URL
        self.api_client.force_authenticate(user=self.admin)
        short_url = ShortURL.objects.get(short_code='collab123')
        update_data = {
            'original_url': 'https://updated-collaboration-example.com',
            'short_code': 'collab123'
        }
        response = self.api_client.put(f'/api/short-urls/{short_url.id}/', update_data)
        assert response.status_code == status.HTTP_200_OK
        
        # Viewer can see the updated URL
        self.api_client.force_authenticate(user=self.viewer)
        response = self.api_client.get(f'/api/short-urls/{short_url.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['original_url'] == 'https://updated-collaboration-example.com'


class TestErrorHandlingIntegration(TestCase):
    """Test error handling across the application"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        self.api_client = APIClient()
        
        self.user = UserFactory()
        self.organization = OrganizationFactory(created_by=self.user)
        AdminMembershipFactory(organization=self.organization, user=self.user)
        self.namespace = NamespaceFactory(organization=self.organization)
    
    def test_error_handling_flow(self):
        """Test error handling in various scenarios"""
        self.api_client.force_authenticate(user=self.user)
        
        # Test invalid namespace
        url_data = {
            'namespace': 99999,  # Non-existent namespace
            'original_url': 'https://example.com',
            'short_code': 'test123'
        }
        response = self.api_client.post('/api/short-urls/', url_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Test duplicate short code
        ShortURLFactory(namespace=self.namespace, short_code='duplicate')
        url_data = {
            'namespace': self.namespace.id,
            'original_url': 'https://example.com',
            'short_code': 'duplicate'  # Duplicate code
        }
        response = self.api_client.post('/api/short-urls/', url_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Test invalid URL
        url_data = {
            'namespace': self.namespace.id,
            'original_url': 'not-a-url',
            'short_code': 'test123'
        }
        response = self.api_client.post('/api/short-urls/', url_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Test non-existent short URL redirect
        response = self.client.get('/r/nonexistent')
        assert response.status_code == 404
        
        # Test expired URL redirect
        expired_url = ShortURLFactory(
            namespace=self.namespace,
            short_code='expired123',
            expires_at=timezone.now() - timedelta(days=1)
        )
        response = self.client.get('/r/expired123')
        assert response.status_code == 410


class TestPerformanceIntegration(TestCase):
    """Test performance with large datasets"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        self.api_client = APIClient()
        
        self.user = UserFactory()
        self.organization = OrganizationFactory(created_by=self.user)
        AdminMembershipFactory(organization=self.organization, user=self.user)
        self.namespace = NamespaceFactory(organization=self.organization)
    
    def test_performance_with_many_urls(self):
        """Test performance with many short URLs"""
        self.api_client.force_authenticate(user=self.user)
        
        # Create many short URLs
        urls = []
        for i in range(100):
            url = ShortURLFactory(
                namespace=self.namespace,
                short_code=f'perf{i}',
                original_url=f'https://perf{i}.example.com',
                created_by=self.user
            )
            urls.append(url)
        
        # Test listing URLs
        response = self.api_client.get('/api/short-urls/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 100
        
        # Test redirecting to URLs
        for i in range(10):  # Test subset for performance
            response = self.client.get(f'/r/perf{i}')
            assert response.status_code == 302
            assert response.url == f'https://perf{i}.example.com'
    
    def test_performance_with_many_organizations(self):
        """Test performance with many organizations"""
        self.api_client.force_authenticate(user=self.user)
        
        # Create many organizations
        organizations = []
        for i in range(50):
            org = OrganizationFactory(created_by=self.user, name=f'Org {i}')
            organizations.append(org)
        
        # Test listing organizations
        response = self.api_client.get('/api/organizations/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 51  # 50 created + 1 from setup
    
    def test_performance_with_many_members(self):
        """Test performance with many organization members"""
        # Create many members
        members = []
        for i in range(100):
            member = UserFactory()
            OrganizationMembershipFactory(
                organization=self.organization,
                user=member,
                role=OrganizationMembership.Role.VIEWER
            )
            members.append(member)
        
        # Test listing members
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.get(f'/api/organizations/{self.organization.id}/members/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 101  # 100 created + 1 admin
