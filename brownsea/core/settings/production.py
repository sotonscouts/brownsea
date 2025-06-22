from .base import *  # noqa
import os

# Explicitly disable debug mode in production
DEBUG = False

# Production Security configuration

# https://docs.djangoproject.com/en/stable/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = True

# https://docs.djangoproject.com/en/stable/ref/settings/#session-cookie-secure
SESSION_COOKIE_SECURE = True

# django-crispy-forms
# https://github.com/django-crispy-forms/django-crispy-forms
CRISPY_FAIL_SILENTLY = True

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Django Vite configuration
DJANGO_VITE = {
    "default": {
        "dev_mode": False,
        "manifest_path": os.path.join(PROJECT_DIR, "static", "dist", ".vite", "manifest.json"),  # noqa: F405
        "static_url_prefix": "dist",
    }
}
