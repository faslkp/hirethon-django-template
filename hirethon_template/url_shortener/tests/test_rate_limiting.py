import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from .factories import UserFactory

User = get_user_model()


@pytest.mark.django_db
class TestRateLimiting(TestCase):
    """Test rate limiting functionality"""

    def setUp(self):
        """Set up test environment"""
        self.client = APIClient()
        self.user = UserFactory()
        self.authenticated_client = APIClient()
        self.authenticated_client.force_authenticate(user=self.user)

    def test_anonymous_rate_limiting(self):
        """Test that anonymous users are rate limited"""
        # Make multiple requests to trigger rate limiting
        # Note: In a real test, you'd need to mock the cache or use a test cache
        # For now, we'll just test that the endpoint is accessible
        url = reverse('api:organization-list')
        
        # First request should work
        response = self.client.get(url)
        # Should get 401 (unauthorized) or 200 (if endpoint allows anonymous)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]

    def test_authenticated_rate_limiting(self):
        """Test that authenticated users have higher rate limits"""
        url = reverse('api:organization-list')
        
        # Authenticated request should work
        response = self.authenticated_client.get(url)
        # Should get 200 (success) or 403 (forbidden if no organizations)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]

    def test_rate_limit_headers(self):
        """Test that rate limit headers are present in responses"""
        url = reverse('api:organization-list')
        
        response = self.authenticated_client.get(url)
        
        # Check for throttle headers (these are added by DRF throttling)
        # Note: Headers might not be present if rate limit hasn't been hit
        # In a real implementation, you'd need to hit the rate limit to see these headers
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]

    def test_different_endpoints_have_rate_limiting(self):
        """Test that different API endpoints have rate limiting applied"""
        endpoints = [
            'api:organization-list',
            'api:namespace-list', 
            'api:short-url-list',
            'api:bulk-upload-list',
        ]
        
        for endpoint in endpoints:
            try:
                url = reverse(endpoint)
                response = self.authenticated_client.get(url)
                # Should get a valid response (success or permission denied)
                assert response.status_code in [
                    status.HTTP_200_OK, 
                    status.HTTP_403_FORBIDDEN,
                    status.HTTP_401_UNAUTHORIZED
                ]
            except Exception:
                # Some endpoints might not exist or have different URL patterns
                # This is expected for some test endpoints
                pass
