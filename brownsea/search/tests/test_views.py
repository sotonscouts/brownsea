import pytest
from bs4 import BeautifulSoup
from django.urls import reverse

from brownsea.factories import InfoPageFactory


@pytest.mark.django_db
def test_search_redirects_anonymous_users_to_login(client):
    response = client.get(reverse("search"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


@pytest.mark.django_db
def test_authenticated_users_can_access_search(authenticated_client):
    response = authenticated_client.get(reverse("search"))

    assert response.status_code == 200


def search(client, **params):
    response = client.get(reverse("search"), params)
    soup = BeautifulSoup(response.content, "html.parser")
    results = [a.find("h3").get_text(strip=True) for a in soup.select("div.list-group a.list-group-item")]
    return response, soup, results


def test_search_without_a_query_shows_no_results(authenticated_client, site_tree):
    InfoPageFactory(parent=site_tree["home"], title="Camping guide")

    response, soup, results = search(authenticated_client)

    assert response.status_code == 200
    assert results == []
    assert "No results found" not in soup.get_text()


def test_search_lists_matching_pages_with_their_introduction(authenticated_client, site_tree):
    page = InfoPageFactory(parent=site_tree["home"], title="Camping guide", introduction="Everything about tents")
    InfoPageFactory(parent=site_tree["home"], title="Kayaking guide")

    response, soup, results = search(authenticated_client, query="camping")

    assert results == ["Camping guide"]
    link = soup.select_one("div.list-group a.list-group-item")
    assert link["href"] == page.url
    assert "Everything about tents" in link.get_text()
    assert "1 result found" in soup.get_text()


def test_search_says_when_nothing_matches(authenticated_client, site_tree):
    InfoPageFactory(parent=site_tree["home"], title="Camping guide")

    response, soup, results = search(authenticated_client, query="zeppelin")

    assert results == []
    assert 'No results found for "zeppelin"' in soup.get_text()


def test_search_ignores_unpublished_pages(authenticated_client, site_tree):
    InfoPageFactory(parent=site_tree["home"], title="Secret camping plans", live=False)

    _, _, results = search(authenticated_client, query="camping")

    assert results == []


def test_search_is_paginated(authenticated_client, site_tree, settings):
    settings.APP_SEARCH_RESULTS_PER_PAGE = 2
    for n in range(3):
        InfoPageFactory(parent=site_tree["home"], title=f"Camping guide {n}", slug=f"camping-{n}")

    _, _, first_page = search(authenticated_client, query="camping")
    _, _, second_page = search(authenticated_client, query="camping", page=2)

    assert len(first_page) == 2
    assert len(second_page) == 1
    assert set(first_page) | set(second_page) == {f"Camping guide {n}" for n in range(3)}


@pytest.mark.parametrize(("page", "expected_count"), [("abc", 2), ("99", 1)])
def test_search_falls_back_on_bad_page_numbers(authenticated_client, site_tree, settings, page, expected_count):
    settings.APP_SEARCH_RESULTS_PER_PAGE = 2
    for n in range(3):
        InfoPageFactory(parent=site_tree["home"], title=f"Camping guide {n}", slug=f"camping-{n}")

    _, _, results = search(authenticated_client, query="camping", page=page)

    assert len(results) == expected_count
