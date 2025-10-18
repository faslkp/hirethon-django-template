from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from hirethon_template.users.api.views import UserViewSet
from hirethon_template.url_shortener.api.views import (
    OrganizationViewSet,
    NamespaceViewSet,
    ShortURLViewSet,
    BulkUploadViewSet
)

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)
router.register("organizations", OrganizationViewSet, basename="organization")
router.register("namespaces", NamespaceViewSet, basename="namespace")
router.register("short-urls", ShortURLViewSet, basename="short-url")
router.register("bulk-upload", BulkUploadViewSet, basename="bulk-upload")


app_name = "api"
urlpatterns = router.urls
