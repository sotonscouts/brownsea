from bs4 import BeautifulSoup

from brownsea.factories import InfoPageFactory


def in_page_nav(response):
    nav = BeautifulSoup(response.content, "html.parser").find("nav", id="page-nav")
    if nav is None:
        return None
    return [(a.get_text(strip=True), a["href"]) for a in nav.find_all("a")]


def test_three_headings_show_the_in_page_navigation(authenticated_client, site_tree):
    page = InfoPageFactory(
        parent=site_tree["home"],
        body__0__heading__heading="First steps",
        body__1__heading__heading="Packing list",
        body__2__heading__heading="After the trip",
    )

    response = authenticated_client.get(page.url)

    assert in_page_nav(response) == [
        ("First steps", "#first-steps"),
        ("Packing list", "#packing-list"),
        ("After the trip", "#after-the-trip"),
    ]


def test_each_link_targets_a_heading_on_the_page(authenticated_client, site_tree):
    page = InfoPageFactory(
        parent=site_tree["home"],
        body__0__heading__heading="First steps",
        body__1__heading__heading="Packing list",
        body__2__heading__heading="After the trip",
    )

    soup = BeautifulSoup(authenticated_client.get(page.url).content, "html.parser")

    for link in soup.select("#page-nav a"):
        assert soup.find("h2", id=link["href"].removeprefix("#")) is not None


def test_fewer_than_three_headings_hides_the_in_page_navigation(authenticated_client, site_tree):
    page = InfoPageFactory(
        parent=site_tree["home"],
        body__0__heading__heading="First steps",
        body__1__heading__heading="Packing list",
    )

    assert in_page_nav(authenticated_client.get(page.url)) is None


def test_pages_without_headings_have_no_in_page_navigation(authenticated_client, site_tree):
    page = InfoPageFactory(parent=site_tree["home"])

    assert in_page_nav(authenticated_client.get(page.url)) is None
