import os

from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "e2e"  # noqa: S105
ALLOWED_HOSTS = ["*"]

SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0

# core/urls.py mounts the debug toolbar URLs whenever the package is importable (it is a dev dependency).
INSTALLED_APPS.append("debug_toolbar")  # noqa: F405

# Never fall back to the developer's database (DATABASE_URL), even if the test database isn't set up in time.
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.path.join(BASE_DIR, "e2e.sqlite3")}}  # noqa: F405

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Serve the compiled frontend (`npm run build`) rather than requiring a running Vite dev server.
DJANGO_VITE = {
    "default": {
        "dev_mode": False,
        "manifest_path": os.path.join(PROJECT_DIR, "static", "dist", ".vite", "manifest.json"),  # noqa: F405
        "static_url_prefix": "dist",
    }
}

# Avoid needing `collectstatic` before running the suite.
STORAGES["staticfiles"] = {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}  # noqa: F405
