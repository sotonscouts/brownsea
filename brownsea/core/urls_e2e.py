from django.conf import settings
from django.urls import path
from django.views.static import serve

from brownsea.core.urls import urlpatterns as base_urlpatterns

# The app only serves media when `DEBUG` is on, which the e2e settings turn off. Media goes before Wagtail's
# catch-all, which is the last pattern.
urlpatterns = [
    *base_urlpatterns[:-1],
    path("media/<path:path>", serve, {"document_root": settings.MEDIA_ROOT}),
    base_urlpatterns[-1],
]
