import datetime

import pytest
from bs4 import BeautifulSoup
from wagtail_factories import ImageFactory

from brownsea.core.factories import AudienceFactory
from brownsea.factories import publish
from brownsea.news.factories import ArticlePageFactory, NewsIndexPageFactory, NewsTopicFactory, NewsTypeFactory


def soup(response):
    return BeautifulSoup(response.content, "html.parser")


def cards(response):
    return [card for card in soup(response).select("main .card") if card.select_one(".card-title")]


def titles(response):
    return [h.get_text(strip=True) for h in soup(response).select("main .card-title")]


@pytest.fixture
def news_index(site_tree):
    return publish(NewsIndexPageFactory(parent=site_tree["home"]))


def article(news_index, title, **kwargs):
    page = ArticlePageFactory(parent=news_index, title=title, slug=title.lower().replace(" ", "-"), **kwargs)
    return publish(page) if page.live else page


def test_shows_its_introduction(authenticated_client, news_index):
    news_index.introduction = "All the news"
    news_index.save()

    assert soup(authenticated_client.get(news_index.url)).select_one(".lead").get_text(strip=True) == "All the news"


def test_lists_articles_newest_first_with_their_date_type_and_link(authenticated_client, news_index):
    older = article(news_index, "Older", publication_date=datetime.date(2026, 1, 1))
    newer = article(
        news_index,
        "Newer",
        publication_date=datetime.date(2026, 2, 3),
        news_type=NewsTypeFactory(name="Announcement"),
    )

    response = authenticated_client.get(news_index.url)

    assert titles(response) == ["Newer", "Older"]
    first, second = cards(response)
    assert first.select_one("a")["href"] == newer.url
    assert second.select_one("a")["href"] == older.url
    assert "3 February 2026" in first.get_text()
    assert "Announcement" in first.get_text()


def test_card_images_are_cropped_so_a_tall_photo_cannot_stretch_the_card(authenticated_client, news_index):
    article(news_index, "Portrait", image=ImageFactory(file__width=400, file__height=1200))

    images = [img["src"] for img in cards(authenticated_client.get(news_index.url))[0].select("img")]

    assert len(images) == 2
    assert ".fill-800x300" in images[0]  # phones
    assert ".fill-200x200" in images[1]  # desktop thumbnail


def test_leaves_out_unpublished_and_hidden_articles(authenticated_client, news_index):
    article(news_index, "Listed")
    article(news_index, "Hidden", show_in_menus=False)
    article(news_index, "Draft", live=False)

    assert titles(authenticated_client.get(news_index.url)) == ["Listed"]


def test_says_when_there_are_no_articles(authenticated_client, news_index):
    assert "No articles have been published yet." in authenticated_client.get(news_index.url).content.decode()


@pytest.fixture
def facets(news_index):
    camping, sailing = (
        NewsTopicFactory(name="Camping", slug="camping"),
        NewsTopicFactory(name="Sailing", slug="sailing"),
    )
    leaders, young = AudienceFactory(name="Leaders", slug="leaders"), AudienceFactory(name="Young people", slug="young")
    update, event = NewsTypeFactory(name="Update", slug="update"), NewsTypeFactory(name="Event", slug="event")
    article(news_index, "Camp update", news_type=update, topics=[camping], audiences=[leaders])
    article(news_index, "Sail update", news_type=update, topics=[sailing], audiences=[young])
    article(news_index, "Camp event", news_type=event, topics=[camping], audiences=[young])
    article(news_index, "Untagged", news_type=event)


def test_filters_by_each_facet(authenticated_client, news_index, facets):
    assert sorted(titles(authenticated_client.get(f"{news_index.url}?type=update"))) == ["Camp update", "Sail update"]
    assert sorted(titles(authenticated_client.get(f"{news_index.url}?topic=camping"))) == ["Camp event", "Camp update"]
    assert titles(authenticated_client.get(f"{news_index.url}?audience=leaders")) == ["Camp update"]


def test_values_in_one_facet_are_alternatives(authenticated_client, news_index, facets):
    response = authenticated_client.get(f"{news_index.url}?topic=camping&topic=sailing")

    assert sorted(titles(response)) == ["Camp event", "Camp update", "Sail update"]


def test_facets_combine(authenticated_client, news_index, facets):
    response = authenticated_client.get(f"{news_index.url}?type=update&topic=camping")

    assert titles(response) == ["Camp update"]


def test_unknown_slugs_are_ignored(authenticated_client, news_index, facets):
    response = authenticated_client.get(f"{news_index.url}?type=nonsense")

    assert len(titles(response)) == 4
    assert "Filter news (" not in response.content.decode()


def test_the_filter_form_ticks_the_chosen_values_and_counts_them(authenticated_client, news_index, facets):
    response = authenticated_client.get(f"{news_index.url}?type=update&topic=camping&topic=sailing")

    checked = {box["id"] for box in soup(response).select("#news-filters input[checked]")}
    assert checked == {"type-update", "topic-camping", "topic-sailing"}
    assert "Filter news (3)" in soup(response).select_one("button[data-bs-target='#news-filters']").get_text()


def test_clear_filters_only_shows_while_filtering(authenticated_client, news_index, facets):
    unfiltered = soup(authenticated_client.get(news_index.url))
    filtered = soup(authenticated_client.get(f"{news_index.url}?type=update"))

    assert unfiltered.find("a", string="Clear filters") is None
    assert filtered.find("a", string="Clear filters")["href"] == news_index.url


def test_says_when_no_articles_match(authenticated_client, news_index, facets):
    response = authenticated_client.get(f"{news_index.url}?type=event&audience=leaders")

    assert "No articles match these filters." in response.content.decode()


def test_the_filter_form_is_left_out_when_there_is_nothing_to_filter_by(authenticated_client, news_index):
    assert soup(authenticated_client.get(news_index.url)).select_one("#news-filters") is None


@pytest.fixture
def three_articles(news_index, settings):
    settings.APP_SEARCH_RESULTS_PER_PAGE = 2
    for day, name in enumerate(["One", "Two", "Three"], start=1):
        article(news_index, name, publication_date=datetime.date(2026, 1, day))


def test_articles_are_paginated(authenticated_client, news_index, three_articles):
    assert titles(authenticated_client.get(news_index.url)) == ["Three", "Two"]
    assert titles(authenticated_client.get(f"{news_index.url}?page=2")) == ["One"]


def test_bad_page_numbers_fall_back(authenticated_client, news_index, three_articles):
    assert titles(authenticated_client.get(f"{news_index.url}?page=nonsense")) == ["Three", "Two"]
    assert titles(authenticated_client.get(f"{news_index.url}?page=99")) == ["One"]


def test_pagination_keeps_the_filters(authenticated_client, news_index, three_articles):
    NewsTypeFactory(slug="update")

    links = soup(authenticated_client.get(f"{news_index.url}?type=update")).select(".pagination a")

    assert all("type=update" in link["href"] for link in links)
