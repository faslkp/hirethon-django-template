import requests
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    """
    Verify Google access token and create/authenticate user
    """
    access_token = request.data.get('access_token')
    
    if not access_token:
        return Response({'error': 'Access token required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify token with Google
    google_user_info = verify_google_token(access_token)
    
    if not google_user_info:
        return Response({'error': 'Invalid Google token'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get or create user
    user, created = get_or_create_user(google_user_info)
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token
    
    return Response({
        'access': str(access_token),
        'refresh': str(refresh),
        'user': {
            'id': user.id,
            'email': user.email,
            'name': user.name,
        }
    })

def verify_google_token(access_token):
    """
    Verify Google access token and return user info
    """
    try:
        response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

def get_or_create_user(google_user_info):
    """
    Get or create user from Google user info
    """
    email = google_user_info.get('email')
    name = google_user_info.get('name', '')
    
    if not email:
        return None, False
    
    # Try to get existing user
    try:
        user = User.objects.get(email=email)
        return user, False
    except User.DoesNotExist:
        # Create new user
        user = User.objects.create_user(
            email=email,
            name=name,
            is_active=True
        )
        return user, True
