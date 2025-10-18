from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UrlShortenerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hirethon_template.url_shortener"
    verbose_name = _("URL Shortener")

    def ready(self):
        try:
            import hirethon_template.url_shortener.signals  # noqa: F401
        except ImportError:
            pass

