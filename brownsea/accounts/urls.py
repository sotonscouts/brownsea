from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]

if settings.SSO_GOOGLE_ENABLED:
    urlpatterns.append(
        path(
            "auth/google/login/",
            views.GoogleLoginCallbackView.as_view(),
            name="google_login_callback",
        )
    )
