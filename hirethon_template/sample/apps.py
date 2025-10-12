from django.apps import AppConfig


class SampleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hirethon_template.sample'

    def ready(self):
        try:
            import hirethon_template.sample.signals  # noqa: F401
        except ImportError:
            pass
