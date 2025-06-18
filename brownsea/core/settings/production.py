from .base import *  # noqa

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
