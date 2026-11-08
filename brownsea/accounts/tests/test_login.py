import pytest
from bs4 import BeautifulSoup
from django.conf import settings
from django.urls import reverse

from brownsea.factories import AdminUserFactory, UserFactory

LOGIN_URL = reverse("accounts:login")


@pytest.fixture
def credentials():
    return {"username": "alice", "password": "password"}


@pytest.fixture
def alice(credentials, site_tree):
    return UserFactory(username=credentials["username"])


def test_login_page_is_available_to_anonymous_users(client, site_tree):
    response = client.get(LOGIN_URL)

    assert response.status_code == 200
    soup = BeautifulSoup(response.content, "html.parser")
    assert soup.find("h1").get_text(strip=True) == "Login"
    assert soup.find("input", attrs={"name": "username"}) is not None
    assert soup.find("input", attrs={"name": "password", "type": "password"}) is not None
    assert soup.find("input", attrs={"type": "submit", "value": "Login"}) is not None


def test_login_page_names_the_site(client, site_tree):
    site = site_tree["site"]
    site.site_name = "Brownsea Intranet"
    site.save()

    response = client.get(LOGIN_URL)

    assert "Login to Brownsea Intranet" in response.content.decode()


def test_valid_credentials_log_the_user_in_and_go_to_the_site_home(client, alice, credentials, site_tree):
    response = client.post(LOGIN_URL, credentials)

    assert response.status_code == 302
    assert response.url == site_tree["home"].url
    assert client.session["_auth_user_id"] == str(alice.pk)


def test_login_returns_to_the_page_the_user_asked_for(client, alice, credentials, site_tree):
    response = client.post(f"{LOGIN_URL}?next=/some/page/", credentials)

    assert response.status_code == 302
    assert response.url == "/some/page/"


@pytest.mark.parametrize("next_url", ["https://evil.example/", "//evil.example/"])
def test_login_does_not_redirect_to_other_sites(client, alice, credentials, site_tree, next_url):
    response = client.post(f"{LOGIN_URL}?next={next_url}", credentials)

    assert response.status_code == 302
    assert response.url == site_tree["home"].url


def test_wrong_password_shows_an_error_and_does_not_log_in(client, alice, site_tree):
    response = client.post(LOGIN_URL, {"username": "alice", "password": "wrong"})

    assert response.status_code == 200
    assert "Please enter a correct username and password" in response.content.decode()
    assert "_auth_user_id" not in client.session


def test_unknown_user_cannot_log_in(client, site_tree):
    response = client.post(LOGIN_URL, {"username": "nobody", "password": "password"})

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session


def test_inactive_users_cannot_log_in(client, credentials, site_tree):
    UserFactory(username=credentials["username"], is_active=False)

    response = client.post(LOGIN_URL, credentials)

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session


def test_logged_in_users_are_sent_on_from_the_login_page(authenticated_client, site_tree):
    response = authenticated_client.get(LOGIN_URL)

    assert response.status_code == 302
    assert response.url == site_tree["home"].url


def test_logged_in_users_follow_next_from_the_login_page(authenticated_client, site_tree):
    response = authenticated_client.get(f"{LOGIN_URL}?next=/some/page/")

    assert response.status_code == 302
    assert response.url == "/some/page/"


def test_logout_ends_the_session_and_redirects(authenticated_client, settings):
    response = authenticated_client.post(reverse("accounts:logout"))

    assert response.status_code == 302
    assert response.url == settings.LOGOUT_REDIRECT_URL
    assert "_auth_user_id" not in authenticated_client.session


def test_logout_requires_a_post(authenticated_client):
    response = authenticated_client.get(reverse("accounts:logout"))

    assert response.status_code == 405
    assert "_auth_user_id" in authenticated_client.session


def test_logout_when_not_logged_in_is_harmless(client, site_tree):
    response = client.post(reverse("accounts:logout"))

    assert response.status_code == 302


def test_google_login_is_not_available_unless_sso_is_enabled(client, site_tree):
    assert not settings.SSO_GOOGLE_ENABLED
    assert client.get("/accounts/auth/google/login/").status_code == 404


# --- The Wagtail admin has its own login ----------------------------------------------------------------------


ADMIN_LOGIN_URL = reverse("wagtailadmin_login")


def test_admin_requires_login(client, site_tree):
    response = client.get("/admin/")

    assert response.status_code == 302
    assert response.url == f"{ADMIN_LOGIN_URL}?next=/admin/"


def test_editors_can_log_in_to_the_admin(client, site_tree, plain_static_files):
    AdminUserFactory(username="editor")

    response = client.post(ADMIN_LOGIN_URL, {"username": "editor", "password": "password"})

    assert response.status_code == 302
    assert response.url == reverse("wagtailadmin_home")
    assert client.get(reverse("wagtailadmin_home")).status_code == 200


def test_ordinary_users_cannot_use_the_admin(client, alice, credentials, site_tree, plain_static_files):
    response = client.post(ADMIN_LOGIN_URL, credentials, follow=True)

    assert response.status_code == 200
    assert "do not have permission to access the admin" in response.content.decode()


def test_admin_rejects_wrong_passwords(client, site_tree, plain_static_files):
    AdminUserFactory(username="editor")

    response = client.post(ADMIN_LOGIN_URL, {"username": "editor", "password": "wrong"})

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session
