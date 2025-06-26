# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import re
from pathlib import Path

import dj_database_url
import environ
import sentry_sdk

env = environ.Env(
    # set casting, default value
    ALLOWED_HOSTS=(list, []),
    SECRET_KEY=(str, ""),
    CSRF_TRUSTED_ORIGINS=(list, []),
    DATABASE_URL=(str, "sqlite:///db.sqlite3"),
    EMAIL_HOST=(str, ""),
    EMAIL_HOST_USER=(str, ""),
    EMAIL_HOST_PASSWORD=(str, ""),
    EMAIL_USE_TLS=(bool, True),
    EMAIL_PORT=(int, 587),
    EMAIL_SUBJECT_PREFIX=(str, "[Brownsea CMS] "),
    SERVER_EMAIL=(str, "brownsea@example.com"),
    WAGTAILADMIN_BASE_URL=(str, ""),
    WAGTAIL_SITE_NAME=(str, "Brownsea Intranet CMS"),
    APP_LOGO_UNIT_NAME=(str, "Brownsea CMS"),
    APP_SHOW_MENU_WHEN_UNAUTHENTICATED=(bool, False),
    APP_SEARCH_RESULTS_PER_PAGE=(int, 10),
    SSO_GOOGLE_ENABLED=(bool, False),
    SSO_ENABLE_PASSWORD_MANAGEMENT=(bool, True),
)

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
BASE_DIR = os.path.dirname(PROJECT_DIR)

# Read .env file
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

DEBUG = False
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
SECRET_KEY = env("SECRET_KEY")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

# Application definition

INSTALLED_APPS = [
    "brownsea.accounts",
    "brownsea.core",
    "brownsea.home",
    "brownsea.navigation",
    "brownsea.news",
    "brownsea.standard_pages",
    "brownsea.search",
    "crispy_forms",
    "crispy_bootstrap5",
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.contrib.settings",
    "wagtail.contrib.table_block",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "modelcluster",
    "taggit",
    "django_filters",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_vite",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

ROOT_URLCONF = "brownsea.core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(PROJECT_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "wagtail.contrib.settings.context_processors.settings",
            ],
        },
    },
]

WSGI_APPLICATION = "brownsea.core.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {"default": dj_database_url.config(conn_max_age=600, default=env("DATABASE_URL"))}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Authentication

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = "/accounts/login/"
WAGTAIL_FRONTEND_LOGIN_URL = LOGIN_URL

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-gb"

TIME_ZONE = "Europe/London"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

STATICFILES_DIRS = [
    os.path.join(PROJECT_DIR, "static"),
]

STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "/static/"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

# Default storage settings, with the staticfiles storage updated.
# See https://docs.djangoproject.com/en/5.2/ref/settings/#std-setting-STORAGES
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    # ManifestStaticFilesStorage is recommended in production, to prevent
    # outdated JavaScript / CSS assets being served from cache
    # (e.g. after a Wagtail upgrade).
    # See https://docs.djangoproject.com/en/5.2/ref/contrib/staticfiles/#manifeststaticfilesstorage
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

if env("AZURE_STORAGE_CONNECTION_STRING", default=None) is not None:
    STORAGES["default"] = {
        "BACKEND": "storages.backends.azure_storage.AzureStorage",
        "OPTIONS": {
            "connection_string": env("AZURE_STORAGE_CONNECTION_STRING"),
            "azure_container": env("AZURE_STORAGE_CONTAINER_NAME"),
            "location": "",  # Store in root of container
            "expiration_secs": 3600,
        },
    }


# http://whitenoise.evans.io/en/stable/django.html#WHITENOISE_IMMUTABLE_FILE_TEST
def immutable_file_test(path, url):
    # Match vite (rollup)-generated hashes, à la, `some_file-CSliV9zW.js`
    return re.match(r"^.+[.-][0-9a-zA-Z_-]{8,12}\..+$", url)


WHITENOISE_IMMUTABLE_FILE_TEST = immutable_file_test

# Django sets a maximum of 1000 fields per form by default, but particularly complex page models
# can exceed this limit within Wagtail's page editor.
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000

# Email settings
# https://docs.djangoproject.com/en/5.2/topics/email/
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")
EMAIL_SUBJECT_PREFIX = env("EMAIL_SUBJECT_PREFIX")
SERVER_EMAIL = env("SERVER_EMAIL")
DEFAULT_FROM_EMAIL = SERVER_EMAIL
WAGTAILADMIN_NOTIFICATION_FROM_EMAIL = SERVER_EMAIL
WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS = False

# Search
# https://docs.wagtail.org/en/stable/topics/search/backends.html
WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.search.backends.database",
    }
}

# Base URL to use when referring to full URLs within the Wagtail admin backend -
# e.g. in notification emails. Don't include '/admin' or a trailing slash
WAGTAILADMIN_BASE_URL = os.environ.get("WAGTAILADMIN_BASE_URL", "http://localhost:8000")

# Allowed file extensions for documents in the document library.
# This can be omitted to allow all files, but note that this may present a security risk
# if untrusted users are allowed to upload files -
# see https://docs.wagtail.org/en/stable/advanced_topics/deploying.html#user-uploaded-files
WAGTAILDOCS_EXTENSIONS = [
    "csv",
    "docx",
    "key",
    "odt",
    "pdf",
    "pptx",
    "rtf",
    "txt",
    "xlsx",
    "zip",
]


WAGTAILADMIN_RICH_TEXT_EDITORS = {
    "default": {
        "WIDGET": "wagtail.admin.rich_text.DraftailRichTextArea",
        "OPTIONS": {"features": ["h3", "h4", "ol", "ul", "bold", "italic", "link"]},
    }
}

WAGTAIL_PASSWORD_REQUIRED_TEMPLATE = "pages/wagtail/password_required.html"  # noqa: S105

# Crispy forms

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# SSO
SSO_GOOGLE_ENABLED = env("SSO_GOOGLE_ENABLED", default=False)
if SSO_GOOGLE_ENABLED:
    SSO_GOOGLE_CLIENT_ID = env("SSO_GOOGLE_CLIENT_ID")
    SSO_GOOGLE_CLIENT_SECRET = env("SSO_GOOGLE_CLIENT_SECRET")
    SSO_GOOGLE_CONFIGURATION_URL = env("SSO_GOOGLE_CONFIGURATION_URL")

# Password management
SSO_ENABLE_PASSWORD_MANAGEMENT = env("SSO_ENABLE_PASSWORD_MANAGEMENT")
WAGTAIL_PASSWORD_MANAGEMENT_ENABLED = SSO_ENABLE_PASSWORD_MANAGEMENT
WAGTAIL_PASSWORD_RESET_ENABLED = SSO_ENABLE_PASSWORD_MANAGEMENT
WAGTAILUSERS_PASSWORD_ENABLED = SSO_ENABLE_PASSWORD_MANAGEMENT
WAGTAILUSERS_PASSWORD_REQUIRED = SSO_ENABLE_PASSWORD_MANAGEMENT
WAGTAIL_EMAIL_MANAGEMENT_ENABLED = SSO_ENABLE_PASSWORD_MANAGEMENT

# Sentry
SENTRY_DSN = env("SENTRY_DSN", default=None)

if SENTRY_DSN:
    SENTRY_ENVIRONMENT = env("SENTRY_ENVIRONMENT")
    SENTRY_TRACES_SAMPLE_RATE = env("SENTRY_TRACES_SAMPLE_RATE", default=0.1)
    SENTRY_SEND_DEFAULT_PII = env("SENTRY_SEND_DEFAULT_PII", default=True)

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENVIRONMENT,
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        send_default_pii=SENTRY_SEND_DEFAULT_PII,
    )

# App Specific Settings
LOGOUT_REDIRECT_URL = env("LOGOUT_REDIRECT_URL")
WAGTAIL_SITE_NAME = env("WAGTAIL_SITE_NAME")
APP_LOGO_UNIT_NAME = env("APP_LOGO_UNIT_NAME")
APP_SHOW_MENU_WHEN_UNAUTHENTICATED = env("APP_SHOW_MENU_WHEN_UNAUTHENTICATED")
APP_SEARCH_RESULTS_PER_PAGE = env("APP_SEARCH_RESULTS_PER_PAGE")
