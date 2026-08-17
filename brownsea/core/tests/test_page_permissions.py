from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from wagtail.models import PageViewRestriction

from brownsea.core.magic_links import build_magic_link_url, sign_magic_link
from brownsea.core.models import PageAccessLevel, PageMagicLink
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


@pytest.fixture
def magic_link_page(info_page):
    info_page.access_level = PageAccessLevel.MAGIC_LINK
    info_page.save_revision().publish()
    return info_page


@pytest.fixture
def active_magic_link(magic_link_page, user):
    return PageMagicLink.objects.create(page=magic_link_page, label="Camp invite", created_by=user)


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
def test_magic_link_setting_requires_login_without_token(client, magic_link_page):
    response = client.get(magic_link_page.url)

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


@pytest.mark.django_db
def test_valid_magic_link_token_grants_access(client, magic_link_page, active_magic_link):
    share_url = build_magic_link_url(active_magic_link)
    token = share_url.split("access=")[1]

    response = client.get(magic_link_page.url, {"access": token})

    assert response.status_code == 302
    assert response.url == magic_link_page.url

    follow_up = client.get(magic_link_page.url)
    assert follow_up.status_code == 200
    assert magic_link_page.title.encode() in follow_up.content


@pytest.mark.django_db
def test_inherited_magic_link_access(client, site_tree, user):
    section = publish(
        InfoPageFactory(
            parent=site_tree["home"],
            title="Shared section",
            slug="shared-section",
            access_level=PageAccessLevel.MAGIC_LINK,
        )
    )
    child = publish(
        InfoPageFactory(
            parent=section,
            title="Shared child page",
            slug="shared-child-page",
        )
    )
    magic_link = PageMagicLink.objects.create(page=section, created_by=user)
    share_url = build_magic_link_url(magic_link)
    token = share_url.split("access=")[1]

    response = client.get(child.url, {"access": token})
    assert response.status_code == 302

    follow_up = client.get(child.url)
    assert follow_up.status_code == 200
    assert child.title.encode() in follow_up.content


@pytest.mark.django_db
def test_revoked_magic_link_denies_access(client, magic_link_page, active_magic_link):
    share_url = build_magic_link_url(active_magic_link)
    token = share_url.split("access=")[1]

    active_magic_link.revoke()

    response = client.get(magic_link_page.url, {"access": token})
    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


@pytest.mark.django_db
def test_expired_magic_link_denies_access(client, magic_link_page, user):
    magic_link = PageMagicLink.objects.create(
        page=magic_link_page,
        expires_at=timezone.now() - timedelta(minutes=1),
        created_by=user,
    )
    token = sign_magic_link(magic_link)

    response = client.get(magic_link_page.url, {"access": token})
    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


@pytest.mark.django_db
def test_session_access_is_removed_when_link_is_revoked(client, magic_link_page, active_magic_link):
    share_url = build_magic_link_url(active_magic_link)
    token = share_url.split("access=")[1]
    client.get(magic_link_page.url, {"access": token})

    active_magic_link.revoke()

    response = client.get(magic_link_page.url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_create_magic_link_view(client, magic_link_page):
    user = UserFactory(is_staff=True, is_superuser=True)
    client.force_login(user)

    response = client.post(
        reverse("core:magic_links_create", args=[magic_link_page.id]),
        {"label": "Volunteers"},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    assert response.status_code == 200
    assert PageMagicLink.objects.filter(page=magic_link_page, label="Volunteers").exists()
    assert b"Volunteers" in response.content


@pytest.mark.django_db
def test_revoke_magic_link_view(client, magic_link_page, active_magic_link):
    user = UserFactory(is_staff=True, is_superuser=True)
    client.force_login(user)

    response = client.post(
        reverse("core:magic_links_revoke", args=[magic_link_page.id, active_magic_link.token_id]),
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    assert response.status_code == 204
    active_magic_link.refresh_from_db()
    assert active_magic_link.revoked_at is not None
