import datetime

import pytest
from bs4 import BeautifulSoup
from wagtail.models import Page
from wagtail_factories import ImageFactory

from brownsea.core.factories import AudienceFactory
from brownsea.factories import HomePageFactory, InfoPageFactory, publish
from brownsea.news.factories import (
    ArticlePageFactory,
    NewsIndexPageFactory,
    NewsTopicFactory,
    NewsTypeFactory,
)


def soup(response):
    return BeautifulSoup(response.content, "html.parser")


@pytest.fixture
def home(site_tree):
    return site_tree["home"]


@pytest.fixture
def news_index(home):
    return publish(NewsIndexPageFactory(parent=home))


def recent_news_titles(response):
    return [h.get_text(strip=True) for h in soup(response).select(".card .list-group-item h3")]


def test_home_page_can_only_go_under_the_root(home):
    from brownsea.home.models import HomePage

    assert HomePage.can_exist_under(Page.get_first_root_node()) is True
    assert HomePage.can_exist_under(home) is False


def test_shows_its_title_and_introduction(authenticated_client, home):
    home.introduction = "Welcome to the unit"
    home.save()

    page = soup(authenticated_client.get("/"))

    assert page.select_one("title").get_text(strip=True).startswith("Home")
    assert page.select_one(".lead").get_text(strip=True) == "Welcome to the unit"


def test_has_a_search_form_that_searches_the_site(authenticated_client, home):
    form = soup(authenticated_client.get("/")).select_one("main form")

    assert form["action"] == "/search/"
    assert form.select_one("input[name=query]") is not None


def test_has_no_breadcrumbs(authenticated_client, home):
    assert soup(authenticated_client.get("/")).select_one("nav[aria-label=breadcrumb]") is None


def test_logged_out_visitors_are_sent_to_log_in(client, home):
    response = client.get("/")

    assert response.status_code == 302
    assert response["Location"].startswith("/accounts/login/")


def test_public_home_page_is_visible_to_visitors(client, home):
    home.access_level = "public"
    home.save()

    assert client.get("/").status_code == 200


def test_featured_sections_link_to_pages_and_external_sites(authenticated_client, home):
    target = InfoPageFactory(parent=home, title="Camp guide", slug="camp-guide", introduction="Pitch a tent")
    image = ImageFactory()
    page = HomePageFactory.build(
        body__0__featured_sections__0__page__page=target,
        body__0__featured_sections__0__page__image=image,
        body__0__featured_sections__1__external_link__title="Badges",
        body__0__featured_sections__1__external_link__url="https://badges.example.com/",
        body__0__featured_sections__1__external_link__image=image,
    )
    home.body = page.body
    home.save()

    cards = soup(authenticated_client.get("/")).select(".card")

    assert [(c.select_one(".card-title").get_text(strip=True), c.select_one("a")["href"]) for c in cards] == [
        ("Camp guide", target.url),
        ("Badges", "https://badges.example.com/"),
    ]
    assert all(c.select_one("img") for c in cards)


def test_a_lone_featured_item_takes_the_full_width(authenticated_client, home):
    target = InfoPageFactory(parent=home, title="Camp guide", slug="camp-guide")
    home.body = HomePageFactory.build(
        body__0__featured_sections__0__page__page=target,
        body__0__featured_sections__0__page__image=ImageFactory(),
    ).body
    home.save()

    assert soup(authenticated_client.get("/")).select_one(".card").find_parent(class_="col-12") is not None


def test_link_sections_show_cards_for_pages_and_external_sites(authenticated_client, home):
    target = InfoPageFactory(parent=home, title="Policies", slug="policies", introduction="Our rules")
    home.body = HomePageFactory.build(
        body__0__link_sections__0__page__page=target,
        body__0__link_sections__1__external_link__title="Badges",
        body__0__link_sections__1__external_link__url="https://badges.example.com/",
        body__0__link_sections__1__external_link__description="<p>Order badges</p>",
    ).body
    home.save()

    cards = soup(authenticated_client.get("/")).select(".card")

    assert [(c.select_one(".card-title").get_text(strip=True), c.select_one("a")["href"]) for c in cards] == [
        ("Policies", target.url),
        ("Badges", "https://badges.example.com/"),
    ]
    assert "Our rules" in cards[0].get_text()


def test_body_sections_keep_the_order_they_were_written_in(authenticated_client, home):
    target = InfoPageFactory(parent=home, title="Policies", slug="policies")
    home.body = HomePageFactory.build(
        body__0__link_sections__0__external_link__title="First",
        body__1__featured_sections__0__page__page=target,
        body__1__featured_sections__0__page__image=ImageFactory(),
        body__2__link_sections__0__external_link__title="Last",
    ).body
    home.save()

    sections = soup(authenticated_client.get("/")).select("main .col-12.col-md-8 > div.mb-4")

    assert [s.select_one(".card-title").get_text(strip=True) for s in sections] == ["First", "Policies", "Last"]


def test_no_news_card_without_a_news_index(authenticated_client, home):
    assert recent_news_titles(authenticated_client.get("/")) == []
    assert "Recent News" not in authenticated_client.get("/").content.decode()


def test_recent_news_is_newest_first_and_limited_to_three(authenticated_client, news_index):
    for day in range(1, 5):
        publish(
            ArticlePageFactory(
                parent=news_index, title=f"Day {day}", slug=f"day-{day}", publication_date=datetime.date(2026, 1, day)
            )
        )

    assert recent_news_titles(authenticated_client.get("/")) == ["Day 4", "Day 3", "Day 2"]


def test_recent_news_shows_type_and_date_and_features_the_lead_article(authenticated_client, news_index):
    news_type = NewsTypeFactory(name="Announcement")
    publish(
        ArticlePageFactory(
            parent=news_index,
            title="Lead",
            slug="lead",
            news_type=news_type,
            introduction="Lead introduction",
            publication_date=datetime.date(2026, 3, 5),
            image=ImageFactory(),
        )
    )
    publish(
        ArticlePageFactory(
            parent=news_index,
            title="Older",
            slug="older",
            introduction="Older introduction",
            publication_date=datetime.date(2026, 3, 1),
        )
    )

    items = soup(authenticated_client.get("/")).select(".card .list-group-item")

    assert "5 March 2026" in items[0].get_text()
    assert "Announcement" in items[0].get_text()
    assert items[0].select_one("img") is not None
    assert "Lead introduction" in items[0].get_text()
    assert "Older introduction" not in items[1].get_text()
    assert items[1].select_one("img") is None


def test_view_all_news_links_to_the_news_index(authenticated_client, news_index):
    publish(ArticlePageFactory(parent=news_index))

    footer = soup(authenticated_client.get("/")).select_one(".card-footer a")

    assert footer["href"] == news_index.url


def test_news_filters_narrow_the_card_and_the_view_all_link(authenticated_client, home, news_index):
    topic = NewsTopicFactory(slug="camping")
    audience = AudienceFactory(slug="leaders")
    news_type = NewsTypeFactory(slug="update")
    other_type = NewsTypeFactory(slug="event")
    publish(
        ArticlePageFactory(parent=news_index, title="Match", topics=[topic], audiences=[audience], news_type=news_type)
    )
    publish(ArticlePageFactory(parent=news_index, title="Wrong topic", audiences=[audience], news_type=news_type))
    publish(
        ArticlePageFactory(
            parent=news_index, title="Wrong type", topics=[topic], audiences=[audience], news_type=other_type
        )
    )
    home.news_topics.set([topic])
    home.news_audiences.set([audience])
    home.news_types.set([news_type])
    home.save()

    response = authenticated_client.get("/")

    assert recent_news_titles(response) == ["Match"]
    assert (
        soup(response).select_one(".card-footer a")["href"]
        == f"{news_index.url}?type=update&audience=leaders&topic=camping"
    )
