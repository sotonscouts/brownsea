"""
The child pages block lists the pages below a landing page, leaving out any the page already links to elsewhere in
its body or sidebar, so the same page is not offered twice.
"""

import pytest
from bs4 import BeautifulSoup
from django.test import Client
from django.utils.text import slugify

from brownsea.core.blocks import get_child_pages
from brownsea.core.factories import PageMagicLinkFactory
from brownsea.core.magic_links import build_magic_link_url
from brownsea.core.models import PageAccessLevel
from brownsea.factories import InfoPageFactory, PageViewRestrictionFactory, publish
from brownsea.landing.factories import LandingPageFactory
from brownsea.landing.models import LandingPage

# Where a page can be linked from on a landing page. Each maps a page to the factory arguments that link to it. The
# child pages block is always the first block of the body, so links start at the second.
LINK_LOCATIONS = {
    "link section": lambda page: {"body__1__link_sections__0__page__page": page},
    "featured section": lambda page: {"body__1__featured_sections__0__page__page": page},
    "logo grid": lambda page: {"body__1__logo_grid__0__page__page": page},
    "task tiles": lambda page: {"body__1__task_tiles__0__page__page": page},
    "quick links in the sidebar": lambda page: {"sidebar__0__quick_links__links__0__page__page": page},
}

EXTERNAL_LINKS = {
    "link section": {"body__1__link_sections__0__external_link__title": "Elsewhere"},
    "featured section": {"body__1__featured_sections__0__external_link__title": "Elsewhere"},
    "logo grid": {"body__1__logo_grid__0__external_link__title": "Elsewhere"},
    "task tiles": {"body__1__task_tiles__0__external_link__label": "Elsewhere"},
    "quick links in the sidebar": {"sidebar__0__quick_links__links__0__external_link__title": "Elsewhere"},
}


def child_page_titles(response):
    """The titles in a child pages block that uses the list layout."""
    soup = BeautifulSoup(response.content, "html.parser")
    return [h.get_text(strip=True) for h in soup.select("main .list-group a.list-group-item-action h3")]


def children(parent, *titles, **kwargs):
    return [publish(InfoPageFactory(parent=parent, title=title, slug=slugify(title), **kwargs)) for title in titles]


def lay_out(landing, **fields):
    """Give a landing page a body and sidebar built from factory arguments, with a child pages list first."""
    if not any(key.startswith("body__0__") for key in fields):
        fields["body__0__child_pages__layout"] = "list"
    built = LandingPageFactory.build(**fields)
    landing.body = built.body
    landing.sidebar = built.sidebar
    return publish(landing)


@pytest.fixture
def home(site_tree):
    return site_tree["home"]


@pytest.fixture
def landing(home):
    return lay_out(publish(LandingPageFactory(parent=home, title="Landing", slug="landing")))


# --- Which pages are left out -------------------------------------------------------------------------------------


def test_every_child_is_listed_when_nothing_is_linked(authenticated_client, landing):
    children(landing, "First", "Second")

    assert child_page_titles(authenticated_client.get(landing.url)) == ["First", "Second"]


@pytest.mark.parametrize("location", LINK_LOCATIONS)
def test_a_page_linked_from_the_page_is_left_out_of_the_list(authenticated_client, landing, location):
    linked, _ = children(landing, "Linked", "Other")

    lay_out(landing, **LINK_LOCATIONS[location](linked))

    assert child_page_titles(authenticated_client.get(landing.url)) == ["Other"]


@pytest.mark.parametrize("location", EXTERNAL_LINKS)
def test_external_links_do_not_hide_anything(authenticated_client, landing, location):
    children(landing, "First", "Second")

    lay_out(landing, **EXTERNAL_LINKS[location])

    assert child_page_titles(authenticated_client.get(landing.url)) == ["First", "Second"]


def test_a_page_linked_in_several_places_is_left_out_of_the_list_once(authenticated_client, landing):
    linked, _ = children(landing, "Linked", "Other")

    lay_out(
        landing,
        **LINK_LOCATIONS["link section"](linked),
        **{"body__2__task_tiles__0__page__page": linked},
        **LINK_LOCATIONS["quick links in the sidebar"](linked),
    )

    assert child_page_titles(authenticated_client.get(landing.url)) == ["Other"]
    assert landing.get_linked_page_ids() == [linked.id, linked.id, linked.id]


def test_several_pages_can_be_linked_from_one_place(authenticated_client, landing):
    first, second, third = children(landing, "First", "Second", "Third")

    lay_out(
        landing,
        body__1__link_sections__0__page__page=first,
        body__1__link_sections__1__page__page=third,
    )

    assert child_page_titles(authenticated_client.get(landing.url)) == ["Second"]


def test_the_rest_keep_their_tree_order(authenticated_client, landing):
    _, middle, _ = children(landing, "Zebra", "Mongoose", "Aardvark")

    lay_out(landing, **LINK_LOCATIONS["link section"](middle))

    assert child_page_titles(authenticated_client.get(landing.url)) == ["Zebra", "Aardvark"]


def test_links_to_pages_that_are_not_children_hide_nothing(authenticated_client, home, landing):
    child, other_child = children(landing, "Child", "Other child")
    grandchild = children(child, "Grandchild")[0]
    elsewhere = children(home, "Elsewhere")[0]

    lay_out(
        landing,
        body__1__link_sections__0__page__page=grandchild,
        body__1__link_sections__1__page__page=elsewhere,
        body__1__link_sections__2__page__page=home,
        body__1__link_sections__3__page__page=landing,
    )

    assert child_page_titles(authenticated_client.get(landing.url)) == ["Child", "Other child"]
    assert set(landing.get_linked_page_ids()) == {grandchild.id, elsewhere.id, home.id, landing.id}


def test_a_link_to_a_deleted_page_hides_nothing_and_does_not_break_the_page(authenticated_client, landing):
    doomed, other = children(landing, "Doomed", "Other")
    lay_out(landing, **LINK_LOCATIONS["link section"](doomed))
    doomed.delete()

    response = authenticated_client.get(landing.url)

    assert response.status_code == 200
    assert child_page_titles(response) == ["Other"]
    assert LandingPage.objects.get(pk=landing.pk).get_linked_page_ids() == []


def test_a_link_in_the_body_hides_the_page_from_a_list_further_down(authenticated_client, landing):
    linked, _ = children(landing, "Linked", "Other")

    # The child pages block comes after the links this time.
    lay_out(
        landing,
        body__0__link_sections__0__page__page=linked,
        body__1__child_pages__layout="list",
    )

    assert child_page_titles(authenticated_client.get(landing.url)) == ["Other"]


def test_each_child_pages_block_leaves_out_the_same_pages(authenticated_client, landing):
    linked, _ = children(landing, "Linked", "Other")

    lay_out(
        landing,
        **LINK_LOCATIONS["link section"](linked),
        body__2__child_pages__layout="list",
    )

    assert child_page_titles(authenticated_client.get(landing.url)) == ["Other", "Other"]


def test_the_cards_layout_leaves_out_linked_pages_too(authenticated_client, landing):
    linked, _ = children(landing, "Linked", "Other")

    lay_out(landing, body__0__child_pages__layout="cards", **LINK_LOCATIONS["task tiles"](linked))

    soup = BeautifulSoup(authenticated_client.get(landing.url).content, "html.parser")
    assert [t.get_text(strip=True) for t in soup.select("main .card-title")] == ["Other"]


# --- The block's heading ------------------------------------------------------------------------------------------


def test_the_heading_shows_while_some_pages_are_listed(authenticated_client, landing):
    linked, _ = children(landing, "Linked", "Other")

    lay_out(landing, body__0__child_pages__title="Also in this section", **LINK_LOCATIONS["link section"](linked))

    assert "Also in this section" in authenticated_client.get(landing.url).content.decode()


def test_the_block_disappears_with_its_heading_when_every_page_is_linked_elsewhere(authenticated_client, landing):
    (only,) = children(landing, "Only")

    lay_out(landing, body__0__child_pages__title="Also in this section", **LINK_LOCATIONS["link section"](only))

    response = authenticated_client.get(landing.url)
    assert "Also in this section" not in response.content.decode()
    assert child_page_titles(response) == []


def test_the_block_disappears_with_its_heading_when_there_are_no_children(authenticated_client, landing):
    lay_out(landing, body__0__child_pages__title="Also in this section")

    assert "Also in this section" not in authenticated_client.get(landing.url).content.decode()


# --- Which pages are candidates -----------------------------------------------------------------------------------


def test_only_direct_children_are_listed(authenticated_client, landing):
    (child,) = children(landing, "Child")
    children(child, "Grandchild")

    assert child_page_titles(authenticated_client.get(landing.url)) == ["Child"]


def test_unpublished_children_are_left_out(authenticated_client, landing):
    children(landing, "Live")
    InfoPageFactory(parent=landing, title="Draft", slug="draft", live=False)

    assert child_page_titles(authenticated_client.get(landing.url)) == ["Live"]


def test_children_behind_a_password_or_group_restriction_are_left_out(authenticated_client, landing):
    visible, locked, members_only = children(landing, "Visible", "Locked", "Members")
    PageViewRestrictionFactory(page=locked, password="secret")  # noqa: S106
    PageViewRestrictionFactory(page=members_only, restriction_type="groups")

    assert child_page_titles(authenticated_client.get(landing.url)) == ["Visible"]


def test_get_child_pages_returns_specific_pages_in_tree_order(landing):
    first, second = children(landing, "First", "Second")

    pages = list(get_child_pages(landing))

    assert pages == [first, second]
    assert all(type(page) is type(first) for page in pages)  # specific, so their introductions are available


def test_get_child_pages_is_empty_for_a_page_that_is_not_saved_yet(home):
    assert get_child_pages(LandingPageFactory.build(parent=None)) == []
    assert get_child_pages(None) == []


# --- What counts as linked ----------------------------------------------------------------------------------------


def test_linked_page_ids_come_from_the_body_and_sidebar_including_nested_sections(landing):
    ids = children(landing, "One", "Two", "Three", "Four", "Five")

    lay_out(
        landing,
        body__1__link_sections__0__page__page=ids[0],
        body__2__featured_sections__0__page__page=ids[1],
        body__3__logo_grid__0__page__page=ids[2],
        body__4__task_tiles__0__page__page=ids[3],
        sidebar__0__quick_links__links__0__page__page=ids[4],
    )

    assert landing.get_linked_page_ids() == [page.id for page in ids]


def test_a_page_with_no_links_has_no_linked_page_ids(landing):
    children(landing, "Child")

    assert landing.get_linked_page_ids() == []


# --- Pages hidden from menus -------------------------------------------------------------------------------------


def test_children_hidden_from_menus_are_left_out_like_in_every_other_listing(authenticated_client, landing):
    children(landing, "Listed")
    children(landing, "Hidden", show_in_menus=False)

    assert child_page_titles(authenticated_client.get(landing.url)) == ["Listed"]


# --- Who is shown which children ----------------------------------------------------------------------------------


@pytest.fixture
def public_landing(home):
    return lay_out(
        publish(LandingPageFactory(parent=home, title="Landing", slug="landing", access_level=PageAccessLevel.PUBLIC))
    )


@pytest.fixture
def mixed_children(public_landing):
    """One child for each access level; the unmarked one inherits the landing page's public access."""
    return {
        "inherits": children(public_landing, "Inherits")[0],
        "public": children(public_landing, "Public", access_level=PageAccessLevel.PUBLIC)[0],
        "members": children(
            public_landing, "Members", access_level=PageAccessLevel.LOGGED_IN, introduction="Members only"
        )[0],
        "shared": children(public_landing, "Shared", access_level=PageAccessLevel.MAGIC_LINK)[0],
    }


def test_visitors_are_only_shown_children_they_can_open(public_landing, mixed_children):
    response = Client().get(public_landing.url)

    assert response.status_code == 200
    assert child_page_titles(response) == ["Inherits", "Public"]
    assert "Members only" not in response.content.decode()


def test_logged_in_users_are_shown_every_child(client, public_landing, mixed_children, user):
    client.force_login(user)

    assert child_page_titles(client.get(public_landing.url)) == ["Inherits", "Public", "Members", "Shared"]


def test_a_visitor_with_a_magic_link_to_a_child_is_shown_it(public_landing, mixed_children):
    visitor = Client()
    link = PageMagicLinkFactory(page=mixed_children["shared"])

    assert child_page_titles(visitor.get(public_landing.url)) == ["Inherits", "Public"]
    visitor.get(build_magic_link_url(link))

    assert child_page_titles(visitor.get(public_landing.url)) == ["Inherits", "Public", "Shared"]


def test_a_revoked_magic_link_does_not_show_its_child(public_landing, mixed_children):
    visitor = Client()
    link = PageMagicLinkFactory(page=mixed_children["shared"])
    visitor.get(build_magic_link_url(link))
    link.revoke()

    assert child_page_titles(visitor.get(public_landing.url)) == ["Inherits", "Public"]


def test_get_child_pages_without_a_request_does_not_filter_by_access(public_landing, mixed_children):
    assert [page.title for page in get_child_pages(public_landing)] == ["Inherits", "Public", "Members", "Shared"]
