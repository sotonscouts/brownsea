from .base import *  # noqa: F403

DEBUG = True
SECRET_KEY = "foo"  # noqa: S105

# Disable HTTPS redirect and HSTS header in development
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0

# Send emails to console in development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DJANGO_VITE = {
    "default": {
        "dev_mode": DEBUG,  # noqa: F405 # type: ignore
        "dev_server_port": 5173,
        "static_url_prefix": "dist",
    }
}

# Set up debug toolbar
INSTALLED_APPS.append("debug_toolbar")  # noqa
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa
INTERNAL_IPS = ["127.0.0.1"]


def show_toolbar(request):
    """Disable debug toolbar in preview iframes where its markup is unavailable."""
    from debug_toolbar.middleware import show_toolbar as default_show_toolbar

    if request.headers.get("Sec-Fetch-Dest") == "iframe":
        return False

    return default_show_toolbar(request)


DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": "brownsea.core.settings.dev.show_toolbar",
}

# https://github.com/django-crispy-forms/django-crispy-forms
CRISPY_FAIL_SILENTLY = False

try:
    from .local import *  # noqa: F403
except ImportError:
    pass
