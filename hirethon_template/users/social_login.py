from allauth.socialaccount.providers.auth0.views import Auth0OAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from dj_rest_auth.registration.views import SocialLoginView
from dj_rest_auth.serializers import TokenSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view


class GoogleLogin(SocialLoginView):  # if you want to use Implicit Grant, use this
    adapter_class = GoogleOAuth2Adapter


@extend_schema_view(
    post=extend_schema(
        request=SocialLoginSerializer,
        responses={200: TokenSerializer(many=False)},
    )
)
class Auth0Login(SocialLoginView):  # if you want to use Implicit Grant, use this
    adapter_class = Auth0OAuth2Adapter
