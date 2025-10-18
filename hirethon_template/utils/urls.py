from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from dj_rest_auth.views import LoginView, LogoutView, UserDetailsView, PasswordChangeView
from dj_rest_auth.registration.views import RegisterView, VerifyEmailView, ResendEmailVerificationView

# CSRF exempt REST auth URLs
urlpatterns = [
    path('login/', csrf_exempt(LoginView.as_view()), name='rest_login'),
    path('logout/', csrf_exempt(LogoutView.as_view()), name='rest_logout'),
    path('user/', csrf_exempt(UserDetailsView.as_view()), name='rest_user_details'),
    path('password/change/', csrf_exempt(PasswordChangeView.as_view()), name='rest_password_change'),
    path('registration/', csrf_exempt(RegisterView.as_view()), name='rest_register'),
    path('registration/verify-email/', csrf_exempt(VerifyEmailView.as_view()), name='rest_verify_email'),
    path('registration/resend-email/', csrf_exempt(ResendEmailVerificationView.as_view()), name='rest_resend_email'),
]
