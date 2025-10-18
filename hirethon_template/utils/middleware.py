from django.middleware.csrf import CsrfViewMiddleware
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import re


class CustomCsrfMiddleware(CsrfViewMiddleware):
    """
    Custom CSRF middleware that exempts API endpoints from CSRF protection
    when using JWT authentication.
    """
    
    def process_view(self, request, callback, callback_args, callback_kwargs):
        # Skip CSRF for API endpoints that use JWT authentication
        if self._should_skip_csrf(request):
            # Set a flag to skip CSRF processing
            request._dont_enforce_csrf_checks = True
            return None
        
        # Use the parent's CSRF processing for non-API endpoints
        return super().process_view(request, callback, callback_args, callback_kwargs)
    
    def _should_skip_csrf(self, request):
        """
        Determine if CSRF should be skipped for this request.
        """
        # Skip CSRF for API endpoints
        api_patterns = [
            r'^/api/',
            r'^/rest-auth/',
        ]
        
        for pattern in api_patterns:
            if re.match(pattern, request.path):
                return True
        
        # Skip CSRF for session-based login (used for private URLs)
        if request.path == '/auth/login/':
            return True
            
        return False
