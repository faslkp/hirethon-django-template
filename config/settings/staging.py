from .base import env
from .production import *  # noqa

# Override production settings for staging environment
# ------------------------------------------------------------------------------

# GENERAL
# ------------------------------------------------------------------------------
# Set DEBUG to True for easier debugging in staging if needed
DEBUG = env.bool("DJANGO_DEBUG", default=False)

# Update allowed hosts for staging
ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=["staging.example.com"],
)

# CORS Settings for API
# ------------------------------------------------------------------------------
# Allow all origins in staging for easier development/testing
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=True)

# Allow credentials for CORS requests
CORS_ALLOW_CREDENTIALS = True

# Add permissive headers for staging environment
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "cache-control",
    "pragma",
    "x-api-key",
]
# SECURITY
# ------------------------------------------------------------------------------
# Make some security settings more relaxed for staging
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=False)
SECURE_HSTS_SECONDS = 0  # Disabled in staging for easier testing
SECURE_HSTS_PRELOAD = False
SECURE_HSTS_INCLUDE_SUBDOMAINS = False

# API Documentation
# ------------------------------------------------------------------------------
SPECTACULAR_SETTINGS["SERVERS"] = [  # noqa: F405
    {"url": "https://staging.example.com", "description": "Staging server"},
    {"url": "http://localhost:8000", "description": "Local development server"},
]
# Admin Site Customization
# ------------------------------------------------------------------------------
ADMIN_SITE_HEADER = "hirethon-template Admin (Staging)"
ADMIN_SITE_TITLE = "hirethon-template Admin Portal (Staging)"
ADMIN_INDEX_TITLE = "Welcome to hirethon-template Admin Portal (Staging)"

# Your stuff...
# ------------------------------------------------------------------------------
