from authlib.integrations.django_client import OAuth
from django.conf import settings

oauth = OAuth()

if settings.SSO_GOOGLE_ENABLED:
    # Google
    oauth.register(
        "google",
        client_id=settings.SSO_GOOGLE_CLIENT_ID,
        client_secret=settings.SSO_GOOGLE_CLIENT_SECRET,
        server_metadata_url=settings.SSO_GOOGLE_CONFIGURATION_URL,
        client_kwargs={"scope": "openid email profile"},
    )
