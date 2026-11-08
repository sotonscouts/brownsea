import pytest
from bs4 import BeautifulSoup

from brownsea.factories import IndexPageFactory, InfoPageFactory


def breadcrumbs(response):
    nav = BeautifulSoup(response.content, "html.parser").find("nav", attrs={"aria-label": "breadcrumb"})
    if nav is None:
        return None
    return [(a.get_text(strip=True), a["href"]) for a in nav.find_all("a")]


def test_the_home_page_has_no_breadcrumbs(authenticated_client, site_tree):
    assert breadcrumbs(authenticated_client.get("/")) is None


def test_pages_below_home_show_the_trail_back_to_home(authenticated_client, site_tree):
    page = InfoPageFactory(parent=site_tree["home"], title="Guides", slug="guides")

    response = authenticated_client.get(page.url)

    assert breadcrumbs(response) == [("Home", site_tree["home"].url)]


def test_nested_pages_list_every_ancestor_in_order(authenticated_client, site_tree):
    section = IndexPageFactory(parent=site_tree["home"], title="Section", slug="section")
    subsection = IndexPageFactory(parent=section, title="Subsection", slug="subsection")
    page = InfoPageFactory(parent=subsection, title="Details", slug="details")

    response = authenticated_client.get(page.url)

    assert breadcrumbs(response) == [
        ("Home", site_tree["home"].url),
        ("Section", section.url),
        ("Subsection", subsection.url),
    ]


def test_the_current_page_is_not_part_of_the_trail(authenticated_client, site_tree):
    page = InfoPageFactory(parent=site_tree["home"], title="Guides", slug="guides")

    trail = breadcrumbs(authenticated_client.get(page.url))

    assert "Guides" not in [title for title, _ in trail]


@pytest.mark.parametrize("path", ["/accounts/login/"])
def test_non_page_views_have_no_breadcrumbs(client, site_tree, path):
    assert breadcrumbs(client.get(path)) is None
