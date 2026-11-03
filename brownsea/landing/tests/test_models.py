import json

import pytest

from brownsea.core.blocks import get_child_pages
from brownsea.factories import InfoPageFactory, publish
from brownsea.landing.factories import LandingPageFactory


def stream(*blocks):
    """Raw stream data, as stored, from (type, value) pairs."""
    return json.dumps([{"type": t, "value": v, "id": f"block-{i}"} for i, (t, v) in enumerate(blocks)])


@pytest.fixture
def landing_page(site_tree):
    return publish(LandingPageFactory(parent=site_tree["home"], title="Landing", slug="landing"))


def info_child(parent, slug, **kwargs):
    return publish(InfoPageFactory(parent=parent, title=slug.title(), slug=slug, **kwargs))


@pytest.mark.django_db
def test_linked_page_ids_cover_body_and_sidebar(landing_page):
    in_logos = info_child(landing_page, "logo")
    in_links = info_child(landing_page, "link")
    in_tiles = info_child(landing_page, "tile")
    in_quick_links = info_child(landing_page, "quick")
    other = info_child(landing_page, "other")

    landing_page.body = stream(
        (
            "logo_grid",
            [
                {"type": "page", "id": "a", "value": {"page": in_logos.id, "image": None}},
                {
                    "type": "external_link",
                    "id": "b",
                    "value": {"url": "https://example.org", "title": "x", "image": None},
                },
            ],
        ),
        ("link_sections", [{"type": "page", "id": "c", "value": {"page": in_links.id}}]),
        (
            "task_tiles",
            [{"type": "page", "id": "d", "value": {"page": in_tiles.id, "icon": "help", "label": "Get help"}}],
        ),
    )
    landing_page.sidebar = stream(
        (
            "quick_links",
            {"heading": "Quick links", "links": [{"type": "page", "id": "e", "value": {"page": in_quick_links.id}}]},
        )
    )

    ids = landing_page.get_linked_page_ids()

    assert {in_logos.id, in_links.id, in_tiles.id, in_quick_links.id} <= set(ids)
    assert other.id not in ids


@pytest.mark.django_db
def test_child_pages_skip_pages_linked_elsewhere_and_unpublished_pages(landing_page):
    linked = info_child(landing_page, "linked")
    shown = info_child(landing_page, "shown")
    draft = InfoPageFactory(parent=landing_page, title="Draft", slug="draft", live=False)
    landing_page.body = stream(("link_sections", [{"type": "page", "id": "a", "value": {"page": linked.id}}]))

    titles = [page.title for page in get_child_pages(landing_page)]

    assert titles == [shown.title]
    assert draft.title not in titles


@pytest.mark.django_db
def test_child_pages_of_an_unsaved_page_are_empty():
    from brownsea.landing.models import LandingPage

    assert get_child_pages(LandingPage(title="New")) == []


@pytest.mark.django_db
def test_landing_page_is_full_width_without_a_sidebar(authenticated_client, landing_page):
    info_child(landing_page, "child")
    landing_page.body = stream(("child_pages", {"title": "Read more", "layout": "cards", "show_introductions": True}))
    publish(landing_page)

    response = authenticated_client.get(landing_page.url)

    html = response.content.decode()
    assert response.status_code == 200
    assert "Read more" in html
    assert "col-md-4" not in html
    # No search box on the page itself (the site-wide search in the navigation is separate).
    assert f'action="{landing_page.url}"' not in html
    assert authenticated_client.get(landing_page.url, {"query": "x"}).context_data.get("search_results") is None


@pytest.mark.django_db
def test_landing_page_shows_a_sidebar_when_it_has_content(authenticated_client, landing_page):
    target = info_child(landing_page, "target")
    landing_page.sidebar = stream(
        (
            "quick_links",
            {
                "heading": "Handy links",
                "links": [
                    {"type": "page", "id": "a", "value": {"page": target.id}},
                    {
                        "type": "external_link",
                        "id": "b",
                        "value": {"url": "https://example.org/x", "title": "Elsewhere"},
                    },
                ],
            },
        )
    )
    publish(landing_page)

    html = authenticated_client.get(landing_page.url).content.decode()

    assert "col-md-4" in html
    assert "Handy links" in html
    assert "Elsewhere" in html
    assert 'href="https://example.org/x"' in html


@pytest.mark.django_db
def test_child_pages_list_layout_can_hide_introductions(authenticated_client, landing_page):
    info_child(landing_page, "child", introduction="A distinctive introduction")
    landing_page.body = stream(("child_pages", {"title": "", "layout": "list", "show_introductions": False}))
    publish(landing_page)

    html = authenticated_client.get(landing_page.url).content.decode()

    assert "list-group-item-action" in html
    assert "A distinctive introduction" not in html


@pytest.mark.django_db
def test_task_tiles_render_the_chosen_icon(authenticated_client, landing_page):
    target = info_child(landing_page, "reset")
    landing_page.body = stream(
        (
            "task_tiles",
            [{"type": "page", "id": "a", "value": {"page": target.id, "icon": "password", "label": "Reset it"}}],
        )
    )
    publish(landing_page)

    html = authenticated_client.get(landing_page.url).content.decode()

    assert "Reset it" in html
    assert "bi-key" in html


@pytest.mark.django_db
def test_landing_pages_can_sit_under_landing_pages(landing_page):
    from brownsea.landing.models import LandingPage

    assert LandingPage.can_exist_under(landing_page) is True
    assert LandingPage.can_create_at(landing_page) is True
