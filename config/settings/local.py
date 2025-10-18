from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="mpavRhuUiZRgvOfNNmzOXhnXyn7C5CNQDYjX8YDEFGjTxQyfnSbcxsXNWdqOB0bC",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1"]

# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env("DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")

# Site configuration for invitation emails
SITE_DOMAIN = env("DJANGO_SITE_DOMAIN", default="localhost:5173")  # Frontend URL
SITE_PROTOCOL = env("DJANGO_SITE_PROTOCOL", default="http")

# WhiteNoise
# ------------------------------------------------------------------------------
# http://whitenoise.evans.io/en/latest/django.html#using-whitenoise-in-development
INSTALLED_APPS = ["whitenoise.runserver_nostatic"] + INSTALLED_APPS  # noqa: F405


# AWS S3 BUCKET
# STORAGE
# ------------------------------------------------------------------------------
# Enable S3 for local development
USE_S3 = env.bool("USE_S3", default=True)

if USE_S3:
    # AWS settings
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    AWS_DEFAULT_ACL = None  # Disable ACLs for buckets that don't support them
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_FILE_OVERWRITE = False
    
    # Use S3 for file storage
    DEFAULT_FILE_STORAGE = "hirethon_template.utils.storages.MediaRootS3Boto3Storage"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"


# django-debug-toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa: F405
# https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
    "SHOW_TEMPLATE_CONTEXT": True,
}
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]
if env("USE_DOCKER") == "yes":
    import socket

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]

# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html#configuration
INSTALLED_APPS += ["django_extensions"]  # noqa: F405
# Celery
# ------------------------------------------------------------------------------

# https://docs.celeryq.dev/en/stable/userguide/configuration.html#task-eager-propagates
CELERY_TASK_EAGER_PROPAGATES = True

# Customize admin site
ADMIN_SITE_HEADER = "{} Admin (Development)".format("hirethon_template".title())
ADMIN_SITE_TITLE = "{} Admin Portal (Development)".format("hirethon_template".title())
ADMIN_INDEX_TITLE = "Welcome to {} Admin Portal (Development)".format("hirethon_template".title())

# Your stuff...
# ------------------------------------------------------------------------------

# CORS settings for local development
# ------------------------------------------------------------------------------
# Allow all origins in local development for easier debugging
CORS_ALLOW_ALL_ORIGINS = True

# Alternatively, if you want to be more restrictive, comment above and use:
# CORS_ALLOWED_ORIGINS += [
#     "http://localhost:3000",
#     "http://localhost:5173",  # Vite default port
#     "http://127.0.0.1:3000",
#     "http://127.0.0.1:5173",
# ]

# CSRF settings for local development
# ------------------------------------------------------------------------------
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# Allow JavaScript to read CSRF cookie in development
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'

# Exempt API from CSRF for JWT authentication
# Since we're using JWT tokens for API auth, CSRF is not needed
CSRF_COOKIE_NAME = "csrftoken"
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# CSRF should not apply to API endpoints when using JWT
# This is safe because JWT tokens provide their own protection against CSRF
CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'

# JWT token lifetimes for local development
from datetime import timedelta
SIMPLE_JWT = {
    **SIMPLE_JWT,  # Inherit from base settings
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),  # 1 hour for comfortable development
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),  # 7 days
}