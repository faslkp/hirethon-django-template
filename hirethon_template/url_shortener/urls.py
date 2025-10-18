from django.urls import path
from .api.views import URLRedirectView

app_name = "url_shortener"

urlpatterns = [
    path('', URLRedirectView.as_view(), name='redirect'),
]

