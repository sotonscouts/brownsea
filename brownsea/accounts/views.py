from typing import Any

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import http
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.urls import reverse
from django.views import View
from wagtail.models import Site

from brownsea.accounts.models import SSOProfile

from .oauth_registry import oauth


class LoginView(DjangoLoginView):
    template_name = "pages/accounts/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        form.helper = FormHelper()
        form.helper.form_method = "post"
        form.helper.add_input(Submit("submit", "Login"))
        return context

    def dispatch(self, request: http.HttpRequest, *args: Any, **kwargs: Any) -> http.HttpResponse:
        # Redirect a user that is already logged in.
        # Borrowed from django.contrib.auth.views.LoginView.dispatch
        if self.request.user.is_authenticated:
            redirect_to = self.get_success_url()
            if redirect_to == self.request.path:
                raise ValueError(
                    "Redirection loop for authenticated user detected. Check that "
                    "your LOGIN_REDIRECT_URL doesn't point to a login page."
                )
            return http.HttpResponseRedirect(redirect_to)

        # If SSO is enabled, redirect immediately.
        if settings.SSO_GOOGLE_ENABLED and "username" not in request.GET:
            request.session["sso_next"] = self.get_redirect_url()

            redirect_uri = request.build_absolute_uri(reverse("accounts:google_login_callback"))
            return oauth.google.authorize_redirect(request, redirect_uri)

        return super().dispatch(request, *args, **kwargs)

    def get_default_redirect_url(self) -> str:
        site = Site.find_for_request(self.request)
        return site.root_page.get_url()


class GoogleLoginCallbackView(View):
    def get(self, request: http.HttpRequest) -> http.HttpResponseRedirect:
        if not settings.SSO_GOOGLE_ENABLED:
            return http.HttpResponseBadRequest("SSO is not enabled.")

        token = oauth.google.authorize_access_token(request)
        userinfo = token.get("userinfo", {})

        try:
            sub = userinfo["sub"]
        except KeyError:
            return http.HttpResponseBadRequest("Invalid response from SSO.")

        try:
            sso_profile = SSOProfile.objects.get(sub=sub, provider="google")
        except SSOProfile.DoesNotExist:
            user = User.objects.create(username=userinfo["email"])
            sso_profile = SSOProfile.objects.create(sub=sub, provider="google", user=user)

        self.update_user(sso_profile.user, userinfo)

        login(request, sso_profile.user)

        from_session = request.session.pop("sso_next", None)

        redirect_to = from_session or self.get_default_redirect_url()
        return http.HttpResponseRedirect(redirect_to)

    def get_default_redirect_url(self) -> str:
        site = Site.find_for_request(self.request)
        return site.root_page.get_url()

    def update_user(self, user: User, claims: dict[str, bool | str | list[str]]) -> User:
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.username = claims.get("email", claims["sub"])
        user.email = claims.get("email")
        user.save()

        return user
