from datetime import timedelta

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse
from django.utils import timezone

from brownsea.core.factories import PageMagicLinkFactory
from brownsea.core.magic_links import build_magic_link_url, sign_magic_link, unsign_magic_link_token
from brownsea.core.models import PageAccessLevel, PageMagicLink
from brownsea.factories import AdminUserFactory, GroupFactory, IndexPageFactory, InfoPageFactory, UserFactory


@pytest.fixture
def section(site_tree):
    """A magic-link section: nested so that its pages show breadcrumbs (where the Share button lives)."""
    return IndexPageFactory(
        parent=site_tree["home"], title="Camp", slug="camp", access_level=PageAccessLevel.MAGIC_LINK
    )


@pytest.fixture
def camp_page(section):
    return InfoPageFactory(parent=section, title="Kit list", slug="kit-list")


@pytest.fixture
def editor(client, db, plain_static_files):
    user = AdminUserFactory()
    client.force_login(user)
    return user


def panel_url(page):
    return reverse("core:magic_links_panel", args=[page.id])


def create_url(page):
    return reverse("core:magic_links_create", args=[page.id])


# --- The panel, create and revoke endpoints --------------------------------------------------------------------


def test_the_panel_requires_login(client, section):
    response = client.get(panel_url(section))

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


def test_the_panel_is_forbidden_to_users_who_cannot_edit_the_page(authenticated_client, section):
    assert authenticated_client.get(panel_url(section)).status_code == 403


def test_the_panel_is_forbidden_for_pages_that_are_not_magic_link_pages(client, editor, site_tree):
    page = InfoPageFactory(parent=site_tree["home"], access_level=PageAccessLevel.LOGGED_IN)

    assert client.get(panel_url(page)).status_code == 403


def test_the_panel_lists_active_and_inactive_links(client, editor, section):
    PageMagicLinkFactory(page=section, label="Parents")
    PageMagicLinkFactory(page=section, label="Old invite", revoked_at=timezone.now())
    PageMagicLinkFactory(page=section, label="Last camp", expires_at=timezone.now() - timedelta(days=1))

    soup = BeautifulSoup(client.get(panel_url(section)).content, "html.parser")

    rows = soup.select("[data-magic-link-row]")
    assert [row.select_one(".fw-semibold").get_text(strip=True) for row in rows] == ["Parents"]
    assert "Old invite" in soup.get_text()
    assert "(revoked)" in soup.get_text()
    assert "Last camp" in soup.get_text()
    assert "(expired" in soup.get_text()


def test_the_panel_says_when_there_are_no_links(client, editor, section):
    assert "No active magic links yet." in client.get(panel_url(section)).content.decode()


def test_inheriting_pages_can_have_links_too(client, editor, camp_page):
    assert camp_page.access_level == PageAccessLevel.INHERIT

    assert client.get(panel_url(camp_page)).status_code == 200


def test_creating_a_link_stores_its_label_expiry_and_creator(client, editor, section):
    response = client.post(
        create_url(section),
        {"label": "  Parents  ", "expires_at": "2030-01-02T10:30"},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    assert response.status_code == 200
    link = PageMagicLink.objects.get(page=section)
    assert link.label == "Parents"
    assert link.created_by == editor
    assert timezone.localtime(link.expires_at).strftime("%Y-%m-%d %H:%M") == "2030-01-02 10:30"
    assert f"access={sign_magic_link(link)}".encode() in response.content


def test_creating_a_link_without_ajax_goes_back_to_the_page(client, editor, section):
    response = client.post(create_url(section), {"label": "Parents"})

    assert response.status_code == 302
    assert response.url == section.url


def test_creating_a_link_requires_post(client, editor, section):
    assert client.get(create_url(section)).status_code == 405


def test_creating_a_link_is_forbidden_without_edit_permission(authenticated_client, section):
    response = authenticated_client.post(create_url(section), {"label": "Parents"})

    assert response.status_code == 403
    assert not PageMagicLink.objects.exists()


def test_groups_with_edit_permission_can_create_links(client, section):
    from django.contrib.auth.models import Permission
    from wagtail.models import GroupPagePermission

    group = GroupFactory(name="Camp leaders")
    GroupPagePermission.objects.create(
        group=group, page=section, permission=Permission.objects.get(codename="change_page")
    )
    user = UserFactory()
    user.groups.add(group)
    client.force_login(user)

    assert client.get(panel_url(section)).status_code == 200


def test_revoking_requires_the_link_to_belong_to_the_page(client, editor, section, camp_page):
    link = PageMagicLinkFactory(page=section)

    response = client.post(reverse("core:magic_links_revoke", args=[camp_page.id, link.token_id]))

    assert response.status_code == 404
    link.refresh_from_db()
    assert link.revoked_at is None


def test_revoking_without_ajax_goes_back_to_the_page(client, editor, section):
    link = PageMagicLinkFactory(page=section)

    response = client.post(reverse("core:magic_links_revoke", args=[section.id, link.token_id]))

    assert response.status_code == 302
    assert response.url == section.url
    link.refresh_from_db()
    assert not link.is_active


# --- The Share button ------------------------------------------------------------------------------------------


def share_button(response):
    return BeautifulSoup(response.content, "html.parser").find("magic-link-share")


def test_editors_see_the_share_button_on_magic_link_pages(client, editor, camp_page):
    button = share_button(client.get(camp_page.url))

    assert button is not None
    assert button["panel-url"] == panel_url(camp_page)


def test_users_who_cannot_edit_do_not_see_the_share_button(authenticated_client, camp_page):
    assert share_button(authenticated_client.get(camp_page.url)) is None


def test_the_share_button_is_not_shown_on_other_pages(client, editor, site_tree):
    page = InfoPageFactory(parent=site_tree["home"], access_level=PageAccessLevel.LOGGED_IN)

    assert share_button(client.get(page.url)) is None


def test_anonymous_visitors_with_a_link_do_not_see_the_share_button(client, camp_page, section):
    link = PageMagicLinkFactory(page=section)

    response = client.get(f"{camp_page.url}?access={sign_magic_link(link)}", follow=True)

    assert response.status_code == 200
    assert share_button(response) is None


# --- Tokens ----------------------------------------------------------------------------------------------------


def test_tokens_round_trip(section):
    link = PageMagicLinkFactory(page=section)

    assert unsign_magic_link_token(sign_magic_link(link)) == link.token_id


@pytest.mark.parametrize("token", ["", "garbage", "not-a-uuid:signature"])
def test_bad_tokens_are_rejected(token):
    assert unsign_magic_link_token(token) is None


def test_tampered_tokens_do_not_grant_access(client, section):
    link = PageMagicLinkFactory(page=section)
    token = sign_magic_link(link)

    response = client.get(f"{section.url}?access={token[:-2]}xx")

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


def test_a_link_for_one_page_does_not_open_a_sibling(client, section, site_tree):
    other = IndexPageFactory(
        parent=site_tree["home"], title="Other camp", slug="other-camp", access_level=PageAccessLevel.MAGIC_LINK
    )
    link = PageMagicLinkFactory(page=section)

    response = client.get(f"{other.url}?access={sign_magic_link(link)}")

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


def test_a_link_covers_the_pages_below_it(client, section, camp_page):
    link = PageMagicLinkFactory(page=section)

    response = client.get(f"{camp_page.url}?access={sign_magic_link(link)}", follow=True)

    assert response.status_code == 200
    assert response.redirect_chain[-1][0] == camp_page.url
    assert b"Kit list" in response.content


def test_redeeming_a_link_redirects_to_the_clean_url(client, section):
    link = PageMagicLinkFactory(page=section)

    response = client.get(f"{section.url}?access={sign_magic_link(link)}")

    assert response.status_code == 302
    assert response.url == section.url


def test_a_link_to_a_child_does_not_open_its_parent(client, section, camp_page):
    link = PageMagicLinkFactory(page=camp_page)

    response = client.get(f"{section.url}?access={sign_magic_link(link)}")

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


def test_a_link_stops_working_for_pages_that_are_no_longer_magic_link_pages(client, section):
    link = PageMagicLinkFactory(page=section)
    section.access_level = PageAccessLevel.LOGGED_IN
    section.save()

    response = client.get(f"{section.url}?access={sign_magic_link(link)}")

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


def test_links_keep_existing_query_parameters(section, rf):
    link = PageMagicLinkFactory(page=section)

    url = build_magic_link_url(link, rf.get("/", {"utm": "x"}))

    assert url.startswith("http://testserver/camp/?access=")


def test_links_can_expire_in_the_future(section):
    link = PageMagicLinkFactory(page=section, expires_at=timezone.now() + timedelta(days=1))

    assert link.is_active
    assert link in PageMagicLink.objects.active()


def test_expired_and_revoked_links_are_not_active(section):
    expired = PageMagicLinkFactory(page=section, expires_at=timezone.now() - timedelta(seconds=1))
    revoked = PageMagicLinkFactory(page=section, revoked_at=timezone.now())

    assert not expired.is_active
    assert not revoked.is_active
    assert not PageMagicLink.objects.active().exists()


# --- The page editor -------------------------------------------------------------------------------------------


def test_the_admin_shows_the_magic_links_panel_for_magic_link_pages(client, editor, section, plain_static_files):
    response = client.get(reverse("wagtailadmin_pages:edit", args=[section.id]))

    assert response.status_code == 200
    assert "Magic links" in response.content.decode()


def test_the_admin_hides_the_magic_links_panel_for_other_pages(client, editor, site_tree, plain_static_files):
    page = InfoPageFactory(parent=site_tree["home"], access_level=PageAccessLevel.PUBLIC)

    response = client.get(reverse("wagtailadmin_pages:edit", args=[page.id]))

    assert response.status_code == 200
    assert "No active magic links" not in response.content.decode()
