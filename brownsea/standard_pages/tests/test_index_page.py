import pytest
from bs4 import BeautifulSoup

from brownsea.factories import IndexPageFactory, InfoPageFactory


@pytest.fixture
def index_page(site_tree):
    return IndexPageFactory(parent=site_tree["home"], title="Camping", slug="camping", introduction="Under canvas")


def cards(response):
    soup = BeautifulSoup(response.content, "html.parser")
    return [
        (card.select_one(".card-title").get_text(strip=True), card.select_one("a")["href"])
        for card in soup.select(".card")
    ]


def test_index_page_shows_its_introduction(authenticated_client, index_page):
    soup = BeautifulSoup(authenticated_client.get(index_page.url).content, "html.parser")

    assert soup.select_one("main h1").get_text(strip=True) == "Camping"
    assert soup.select_one(".lead").get_text(strip=True) == "Under canvas"


def test_children_are_listed_in_tree_order_with_links(authenticated_client, index_page):
    second = InfoPageFactory(parent=index_page, title="Zebra", slug="zebra")
    first = InfoPageFactory(parent=index_page, title="Aardvark", slug="aardvark")

    assert cards(authenticated_client.get(index_page.url)) == [("Zebra", second.url), ("Aardvark", first.url)]


def test_only_live_children_shown_in_menus_are_listed(authenticated_client, index_page):
    InfoPageFactory(parent=index_page, title="Listed", slug="listed")
    InfoPageFactory(parent=index_page, title="Hidden", slug="hidden", show_in_menus=False)
    InfoPageFactory(parent=index_page, title="Draft", slug="draft", live=False)

    titles = [title for title, _ in cards(authenticated_client.get(index_page.url))]

    assert titles == ["Listed"]


def test_grandchildren_are_not_listed(authenticated_client, index_page):
    child = InfoPageFactory(parent=index_page, title="Child", slug="child")
    InfoPageFactory(parent=child, title="Grandchild", slug="grandchild")

    titles = [title for title, _ in cards(authenticated_client.get(index_page.url))]

    assert titles == ["Child"]


@pytest.fixture
def three_children(index_page, settings):
    settings.APP_SEARCH_RESULTS_PER_PAGE = 2
    for title in ("One", "Two", "Three"):
        InfoPageFactory(parent=index_page, title=title, slug=title.lower())


def test_children_are_paginated(authenticated_client, index_page, three_children):
    first = authenticated_client.get(index_page.url)
    second = authenticated_client.get(index_page.url, {"page": 2})

    assert [title for title, _ in cards(first)] == ["One", "Two"]
    assert [title for title, _ in cards(second)] == ["Three"]


@pytest.mark.parametrize(("page", "expected"), [("abc", ["One", "Two"]), ("99", ["Three"])])
def test_bad_page_numbers_fall_back_to_a_valid_page(authenticated_client, index_page, three_children, page, expected):
    response = authenticated_client.get(index_page.url, {"page": page})

    assert response.status_code == 200
    assert [title for title, _ in cards(response)] == expected
