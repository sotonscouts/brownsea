import pytest
from bs4 import BeautifulSoup
from django.urls import reverse

from brownsea.factories import InfoPageFactory


@pytest.fixture
def info_page(site_tree):
    return InfoPageFactory(
        parent=site_tree["home"],
        title="Trip guide",
        slug="trip-guide",
        introduction="Everything for the weekend away",
        body__0__heading__heading="Before you go",
        body__1__text="<p>Check the <b>weather</b></p>",
        body__2__quote__quote="Always be prepared",
        body__2__quote__author="Baden-Powell",
    )


def soup(response):
    return BeautifulSoup(response.content, "html.parser")


def test_info_page_shows_title_and_introduction(authenticated_client, info_page):
    page = soup(authenticated_client.get(info_page.url))

    assert page.select_one("main h1").get_text(strip=True) == "Trip guide"
    assert page.select_one("#introduction .lead").get_text(strip=True) == "Everything for the weekend away"


def test_title_tag_names_the_page(authenticated_client, info_page):
    assert "Trip guide" in soup(authenticated_client.get(info_page.url)).title.get_text()


def test_body_blocks_are_rendered_in_order(authenticated_client, info_page):
    body = soup(authenticated_client.get(info_page.url)).select_one("#main-content")

    assert [child.name for child in body.find_all(recursive=False)] == ["h2", "p", "figure"]
    assert body.find("h2").get_text(strip=True) == "Before you go"
    assert body.find("b").get_text(strip=True) == "weather"
    assert body.find("blockquote").get_text(strip=True) == "Always be prepared"
    assert body.find("figcaption").get_text(strip=True) == "Baden-Powell"


def test_a_page_with_no_body_still_renders(authenticated_client, site_tree):
    page = InfoPageFactory(parent=site_tree["home"], title="Empty", slug="empty", introduction="Nothing yet")

    response = authenticated_client.get(page.url)

    assert response.status_code == 200
    assert soup(response).select_one("#main-content").get_text(strip=True) == ""


def test_unpublished_pages_are_not_found(authenticated_client, site_tree):
    InfoPageFactory(parent=site_tree["home"], title="Draft", slug="draft", live=False)

    assert authenticated_client.get("/draft/").status_code == 404


@pytest.mark.parametrize("query", ["weekend", "weather", "Before"])
def test_introduction_and_body_are_searchable(authenticated_client, info_page, query):
    response = authenticated_client.get(reverse("search"), {"query": query})

    titles = [h.get_text(strip=True) for h in soup(response).select(".list-group-item h3")]
    assert titles == ["Trip guide"]
