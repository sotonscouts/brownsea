"""Wagtail's own page privacy (password, group and logged-in restrictions), on top of the access levels."""

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse
from wagtail.models import PageViewRestriction

from brownsea.core.models import PageAccessLevel
from brownsea.factories import GroupFactory, InfoPageFactory, PageViewRestrictionFactory, UserFactory

PASSWORD = "secret"  # noqa: S105


@pytest.fixture
def leaders_page(site_tree):
    return InfoPageFactory(
        parent=site_tree["home"], title="Leaders' notes", slug="leaders-notes", access_level=PageAccessLevel.PUBLIC
    )


def submit_password(client, leaders_page, password):
    restriction = leaders_page.get_view_restrictions().get()
    url = reverse("wagtailcore_authenticate_with_password", args=[restriction.id, leaders_page.id])
    return client.post(url, {"password": password, "return_url": leaders_page.url}, follow=True)


def test_the_right_password_shows_the_page(client, leaders_page):
    PageViewRestrictionFactory(page=leaders_page, password=PASSWORD)

    response = submit_password(client, leaders_page, PASSWORD)

    assert response.status_code == 200
    assert "Leaders&#x27; notes" in response.content.decode() or "Leaders' notes" in response.content.decode()
    assert "You need a password" not in response.content.decode()


def test_the_wrong_password_keeps_the_page_locked(client, leaders_page):
    PageViewRestrictionFactory(page=leaders_page, password=PASSWORD)

    response = submit_password(client, leaders_page, "guess")

    assert "You need a password to access this page." in response.content.decode()
    assert BeautifulSoup(response.content, "html.parser").select(".errorlist, .invalid-feedback, .alert-danger")


def test_the_password_is_remembered_for_the_session(client, leaders_page):
    PageViewRestrictionFactory(page=leaders_page, password=PASSWORD)
    submit_password(client, leaders_page, PASSWORD)

    response = client.get(leaders_page.url)

    assert "You need a password" not in response.content.decode()


def test_the_password_form_has_a_continue_button(client, leaders_page):
    PageViewRestrictionFactory(page=leaders_page, password=PASSWORD)

    soup = BeautifulSoup(client.get(leaders_page.url).content, "html.parser")

    assert soup.find("input", attrs={"type": "password"}) is not None
    assert soup.find("input", attrs={"type": "submit", "value": "Continue"}) is not None


def test_logged_in_restriction_sends_anonymous_users_to_login(client, leaders_page):
    PageViewRestrictionFactory(page=leaders_page, restriction_type=PageViewRestriction.LOGIN)

    response = client.get(leaders_page.url)

    assert response.status_code == 302
    assert response.url == f"{reverse('accounts:login')}?next={leaders_page.url}"


def test_group_restriction_lets_members_in(client, leaders_page):
    group = GroupFactory(name="Leaders")
    PageViewRestrictionFactory(page=leaders_page, restriction_type=PageViewRestriction.GROUPS, groups=[group])
    user = UserFactory()
    user.groups.add(group)
    client.force_login(user)

    assert client.get(leaders_page.url).status_code == 200


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known bug: a logged-in user outside the required group is redirected to the login page, which sends "
        "logged-in users straight back to `next`, so the browser loops forever. The login template already has a "
        "'your account doesn't have access' notice for this case, but LoginView never lets it render."
    ),
)
def test_group_restriction_tells_other_logged_in_users_they_lack_access(client, leaders_page):
    group = GroupFactory(name="Leaders")
    PageViewRestrictionFactory(page=leaders_page, restriction_type=PageViewRestriction.GROUPS, groups=[group])
    client.force_login(UserFactory())

    response = client.get(leaders_page.url, follow=True)

    assert response.status_code == 200
    assert "doesn't have access to this page" in response.content.decode()
