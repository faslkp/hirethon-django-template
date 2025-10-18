from rest_framework_simplejwt.authentication import JWTAuthentication
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


class CSRFExemptJWTAuthentication(JWTAuthentication):
    """
    JWT Authentication that exempts CSRF protection.
    """
    
    def authenticate(self, request):
        # Call parent authentication
        result = super().authenticate(request)
        
        # If JWT authentication is successful, exempt CSRF
        if result is not None:
            # Mark the request as exempt from CSRF
            request._dont_enforce_csrf_checks = True
            
        return result
