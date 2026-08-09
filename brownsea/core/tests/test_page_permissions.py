import pytest
from django.urls import reverse
from wagtail.models import PageViewRestriction

from brownsea.core.models import PageAccessLevel
from brownsea.factories import GroupFactory, InfoPageFactory, UserFactory, publish


@pytest.fixture
def info_page(site_tree):
    return publish(
        InfoPageFactory(
            parent=site_tree["home"],
            title="Test info page",
            slug="test-info-page",
        )
    )


@pytest.mark.django_db
def test_anonymous_users_are_redirected_to_login(client, info_page):
    response = client.get(info_page.url)

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


@pytest.mark.django_db
def test_authenticated_users_can_access_pages(authenticated_client, info_page):
    response = authenticated_client.get(info_page.url)

    assert response.status_code == 200
    assert info_page.title.encode() in response.content


@pytest.mark.django_db
def test_login_required_page_redirects_anonymous_users(client, info_page):
    PageViewRestriction.objects.create(
        page=info_page,
        restriction_type=PageViewRestriction.LOGIN,
    )

    response = client.get(info_page.url)

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


@pytest.mark.django_db
def test_login_required_page_is_accessible_to_authenticated_users(authenticated_client, info_page):
    PageViewRestriction.objects.create(
        page=info_page,
        restriction_type=PageViewRestriction.LOGIN,
    )

    response = authenticated_client.get(info_page.url)

    assert response.status_code == 200
    assert info_page.title.encode() in response.content


@pytest.mark.django_db
def test_password_required_page_shows_password_form(client, info_page):
    PageViewRestriction.objects.create(
        page=info_page,
        restriction_type=PageViewRestriction.PASSWORD,
        password="secret",  # noqa: S106
    )

    response = client.get(info_page.url)

    assert response.status_code == 200
    assert b"Password required" in response.content
    assert b"You need a password to access this page." in response.content


@pytest.mark.django_db
def test_group_restricted_page_redirects_users_not_in_group(client, info_page):
    group = GroupFactory(name="Leaders")
    restriction = PageViewRestriction.objects.create(
        page=info_page,
        restriction_type=PageViewRestriction.GROUPS,
    )
    restriction.groups.add(group)

    response = client.get(info_page.url)

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


@pytest.mark.django_db
def test_group_restricted_page_is_accessible_to_group_members(client, info_page):
    group = GroupFactory(name="Leaders")
    user = UserFactory(username="leader")
    user.groups.add(group)
    client.force_login(user)

    restriction = PageViewRestriction.objects.create(
        page=info_page,
        restriction_type=PageViewRestriction.GROUPS,
    )
    restriction.groups.add(group)

    response = client.get(info_page.url)

    assert response.status_code == 200
    assert info_page.title.encode() in response.content


@pytest.mark.django_db
def test_public_section_is_accessible_to_anonymous_users(client, site_tree):
    section = publish(
        InfoPageFactory(
            parent=site_tree["home"],
            title="Public section",
            slug="public-section",
            access_level=PageAccessLevel.PUBLIC,
        )
    )
    child = publish(
        InfoPageFactory(
            parent=section,
            title="Public child page",
            slug="public-child-page",
        )
    )

    response = client.get(child.url)

    assert response.status_code == 200
    assert child.title.encode() in response.content


@pytest.mark.django_db
def test_inherited_logged_in_setting_blocks_anonymous_users(client, site_tree):
    section = publish(
        InfoPageFactory(
            parent=site_tree["home"],
            title="Members section",
            slug="members-section",
            access_level=PageAccessLevel.LOGGED_IN,
        )
    )
    child = publish(
        InfoPageFactory(
            parent=section,
            title="Members child page",
            slug="members-child-page",
        )
    )

    response = client.get(child.url)

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


@pytest.mark.django_db
def test_explicit_public_child_overrides_logged_in_parent(client, site_tree):
    section = publish(
        InfoPageFactory(
            parent=site_tree["home"],
            title="Members section",
            slug="members-section-override",
            access_level=PageAccessLevel.LOGGED_IN,
        )
    )
    child = publish(
        InfoPageFactory(
            parent=section,
            title="Public child page",
            slug="public-child-override",
            access_level=PageAccessLevel.PUBLIC,
        )
    )

    response = client.get(child.url)

    assert response.status_code == 200
    assert child.title.encode() in response.content


@pytest.mark.django_db
def test_magic_link_setting_requires_login_for_now(client, info_page):
    info_page.access_level = PageAccessLevel.MAGIC_LINK
    info_page.save_revision().publish()

    response = client.get(info_page.url)

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))
