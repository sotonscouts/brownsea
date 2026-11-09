import datetime

import pytest
from bs4 import BeautifulSoup
from wagtail.models import Page
from wagtail_factories import ImageFactory

from brownsea.factories import IndexPageFactory, InfoPageFactory, publish
from brownsea.landing.factories import LandingPageFactory
from brownsea.landing.models import LandingPage
from brownsea.news.factories import ArticlePageFactory, NewsIndexPageFactory, NewsTopicFactory, NewsTypeFactory


def soup(response):
    return BeautifulSoup(response.content, "html.parser")


@pytest.fixture
def home(site_tree):
    return site_tree["home"]


def landing(home, **kwargs):
    return publish(LandingPageFactory(parent=home, title="Landing", slug="landing", **kwargs))


def sidebar_news_titles(response):
    return [h.get_text(strip=True) for h in soup(response).select("main .card .list-group-item h3")]


# --- Placement ----------------------------------------------------------------------------------------------------


def test_landing_pages_go_under_the_root_home_index_and_landing_pages(home):
    index = publish(IndexPageFactory(parent=home))

    assert LandingPage.can_exist_under(Page.get_first_root_node()) is True
    assert LandingPage.can_exist_under(home) is True
    assert LandingPage.can_exist_under(index) is True


def test_landing_pages_do_not_go_under_other_pages(home):
    info = publish(InfoPageFactory(parent=home))
    news_index = publish(NewsIndexPageFactory(parent=home))

    assert LandingPage.can_exist_under(info) is False
    assert LandingPage.can_exist_under(news_index) is False


# --- Content ------------------------------------------------------------------------------------------------------


def test_shows_its_title_and_introduction(authenticated_client, home):
    page = landing(home, introduction="Everything for camping")

    response = soup(authenticated_client.get(page.url))

    assert response.select_one("main h1").get_text(strip=True) == "Landing"
    assert response.select_one(".lead").get_text(strip=True) == "Everything for camping"


def test_the_body_keeps_the_order_it_was_written_in(authenticated_client, home):
    page = landing(
        home,
        body__0__heading__heading="First",
        body__1__text="<p>Second</p>",
        body__2__heading__heading="Third",
        body__3__text="<p>Fourth</p>",
    )

    body = soup(authenticated_client.get(page.url)).select_one("main")

    assert [e.get_text(strip=True) for e in body.select("h2:not(.visually-hidden), p:not(.lead)")] == [
        "First",
        "Second",
        "Third",
        "Fourth",
    ]


def test_the_body_is_beside_a_sidebar_only_when_there_is_one(authenticated_client, home):
    plain = landing(home)
    with_sidebar = publish(
        LandingPageFactory(
            parent=home, title="Sidebar", slug="sidebar", sidebar__0__quick_links__links__0__external_link__title="x"
        )
    )

    assert soup(authenticated_client.get(plain.url)).select_one(".col-md-8") is None
    assert soup(authenticated_client.get(with_sidebar.url)).select_one(".col-md-8 .lead") is not None


def test_quick_links_in_the_sidebar_link_to_pages_and_other_sites(authenticated_client, home):
    target = publish(InfoPageFactory(parent=home, title="Policies", slug="policies"))
    page = landing(
        home,
        sidebar__0__quick_links__heading="Handy links",
        sidebar__0__quick_links__links__0__page__page=target,
        sidebar__0__quick_links__links__1__external_link__title="Badges",
        sidebar__0__quick_links__links__1__external_link__url="https://badges.example.com/",
    )

    links = soup(authenticated_client.get(page.url)).select(".col-md-4 .card a")

    assert [(a.get_text(strip=True), a["href"]) for a in links] == [
        ("Policies", target.url),
        ("Badges", "https://badges.example.com/"),
    ]
    assert soup(authenticated_client.get(page.url)).select_one(".col-md-4 .card-header").get_text(strip=True) == (
        "Handy links"
    )


# --- Recent news in the sidebar -----------------------------------------------------------------------------------


@pytest.fixture
def news_index(home):
    return publish(NewsIndexPageFactory(parent=home))


def article(news_index, title, **kwargs):
    return publish(
        ArticlePageFactory(
            parent=news_index, title=title, slug=title.lower().replace(" ", "-"), show_in_menus=True, **kwargs
        )
    )


def test_the_sidebar_shows_the_three_newest_articles(authenticated_client, home, news_index):
    for day in range(1, 5):
        article(news_index, f"Day {day}", publication_date=datetime.date(2026, 1, day))
    page = landing(home, sidebar__0__recent_news=True)

    assert sidebar_news_titles(authenticated_client.get(page.url)) == ["Day 4", "Day 3", "Day 2"]


def test_the_sidebar_news_does_not_feature_a_lead_article(authenticated_client, home, news_index):
    article(news_index, "Lead", image=ImageFactory(), introduction="Lead introduction")
    page = landing(home, sidebar__0__recent_news=True)

    response = authenticated_client.get(page.url)

    assert soup(response).select_one(".card .list-group-item img") is None
    assert "Lead introduction" not in response.content.decode()


def test_the_news_filters_set_on_the_page_narrow_the_sidebar_and_its_view_all_link(
    authenticated_client, home, news_index
):
    topic = NewsTopicFactory(slug="camping")
    update = NewsTypeFactory(slug="update")
    article(news_index, "Match", topics=[topic], news_type=update)
    article(news_index, "Wrong topic", news_type=update)
    page = landing(home, sidebar__0__recent_news=True)
    page.news_topics.set([topic])
    page.news_types.set([update])
    page.save()

    response = authenticated_client.get(page.url)

    assert sidebar_news_titles(response) == ["Match"]
    assert soup(response).select_one(".card-footer a")["href"] == f"{news_index.url}?type=update&topic=camping"


def test_there_is_no_news_card_without_a_news_index(authenticated_client, home):
    page = landing(home, sidebar__0__recent_news=True)

    response = authenticated_client.get(page.url)

    assert response.status_code == 200
    assert sidebar_news_titles(response) == []
    assert "Recent News" not in response.content.decode()
