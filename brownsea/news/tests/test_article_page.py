import datetime

import pytest
from bs4 import BeautifulSoup
from wagtail_factories import ImageFactory

from brownsea.core.factories import AudienceFactory
from brownsea.factories import publish
from brownsea.news.factories import ArticlePageFactory, NewsIndexPageFactory, NewsTopicFactory, NewsTypeFactory
from brownsea.news.models.pages import ArticlePage
from brownsea.people.factories import PersonFactory, PersonRoleFactory


def soup(response):
    return BeautifulSoup(response.content, "html.parser")


@pytest.fixture
def news_index(site_tree):
    return publish(NewsIndexPageFactory(parent=site_tree["home"]))


def make_article(news_index, **kwargs):
    return publish(ArticlePageFactory(parent=news_index, title="Camp news", slug="camp-news", **kwargs))


def test_articles_only_go_under_a_news_index_and_have_no_children(site_tree, news_index):
    assert ArticlePage.can_exist_under(news_index) is True
    assert ArticlePage.can_exist_under(site_tree["home"]) is False
    assert ArticlePage.allowed_subpage_models() == []


def test_shows_its_title_and_introduction(authenticated_client, news_index):
    page = soup(authenticated_client.get(make_article(news_index, introduction="Pitch a tent").url))

    assert page.select_one("main h1").get_text(strip=True) == "Camp news"
    assert page.select_one(".lead").get_text(strip=True) == "Pitch a tent"


def test_shows_the_publication_date_and_type(authenticated_client, news_index):
    article = make_article(
        news_index, publication_date=datetime.date(2026, 3, 5), news_type=NewsTypeFactory(name="Announcement")
    )

    text = soup(authenticated_client.get(article.url)).select_one(".text-muted").get_text(" ", strip=True)

    assert "5 March 2026" in text
    assert "Announcement" in text


def test_the_date_falls_back_to_when_it_was_first_published(authenticated_client, news_index):
    article = make_article(news_index, publication_date=None)
    article.first_published_at = datetime.datetime(2025, 12, 24, 9, 0, tzinfo=datetime.UTC)
    article.save()

    assert "24 December 2025" in authenticated_client.get(article.url).content.decode()


def test_shows_the_author_and_the_role_they_had_when_there_is_one(authenticated_client, news_index):
    sam = PersonFactory(name="Sam Smith", role="Deputy District Commissioner", role__is_current=False)
    then = sam.roles.get()
    PersonRoleFactory(person=sam, title="District Commissioner")
    with_author = make_article(news_index, author_role=then)

    card = soup(authenticated_client.get(with_author.url)).select_one(".card")

    assert card.select_one(".card-title").get_text(strip=True) == "Sam Smith"
    assert card.select_one(".card-text").get_text(strip=True) == "Deputy District Commissioner"


def test_has_no_author_card_without_an_author(authenticated_client, news_index):
    assert soup(authenticated_client.get(make_article(news_index).url)).select_one(".card") is None


def test_audience_and_topic_badges_link_to_the_filtered_news_index(authenticated_client, news_index):
    article = make_article(
        news_index,
        audiences=[AudienceFactory(name="Leaders", slug="leaders")],
        topics=[NewsTopicFactory(name="Camping", slug="camping")],
    )

    badges = soup(authenticated_client.get(article.url)).select(".badge")

    assert [(b.get_text(" ", strip=True), b["href"]) for b in badges] == [
        ("Audience: Leaders", f"{news_index.url}?audience=leaders"),
        ("Topic: Camping", f"{news_index.url}?topic=camping"),
    ]


def test_shows_its_body_in_order(authenticated_client, news_index):
    article = make_article(
        news_index,
        body__0__heading__heading="Before you go",
        body__1__text="<p>Check the weather</p>",
        body__2__heading__heading="When you arrive",
    )

    body = soup(authenticated_client.get(article.url)).select_one("#main-content")

    assert [e.get_text(strip=True) for e in body.find_all(["h2", "p"])] == [
        "Before you go",
        "Check the weather",
        "When you arrive",
    ]


def test_in_page_navigation_needs_three_headings(authenticated_client, news_index):
    few = make_article(news_index, body__0__heading__heading="One", body__1__heading__heading="Two")
    many = publish(
        ArticlePageFactory(
            parent=news_index,
            title="Many",
            slug="many",
            body__0__heading__heading="One",
            body__1__heading__heading="Two",
            body__2__heading__heading="Three",
        )
    )

    assert soup(authenticated_client.get(few.url)).select_one("#page-nav") is None
    nav = soup(authenticated_client.get(many.url)).select_one("#page-nav")
    assert [a.get_text(strip=True) for a in nav.select("a")] == ["One", "Two", "Three"]


def test_shows_the_image_below_the_date_and_topics_cropped_to_a_fixed_shape(authenticated_client, news_index):
    # A tall photo would otherwise push the article off the screen.
    with_image = make_article(news_index, image=ImageFactory(file__width=400, file__height=1200))
    without_image = publish(ArticlePageFactory(parent=news_index, title="Plain", slug="plain"))

    page = soup(authenticated_client.get(with_image.url))

    assert ".fill-800x300" in page.select_one("main img.img-fluid")["src"]
    order = page.select("main .text-muted, main img, main .lead")
    assert [el.name for el in order] == ["div", "img", "p"]  # date and topics, then the image, then the introduction
    assert soup(authenticated_client.get(without_image.url)).select_one("main img") is None


def test_unpublished_articles_cannot_be_seen(authenticated_client, news_index):
    article = make_article(news_index)
    article.unpublish()

    assert authenticated_client.get(article.url).status_code == 404


def test_articles_can_be_found_by_searching_their_introduction(authenticated_client, news_index):
    make_article(news_index, introduction="Lanterns and marshmallows")

    response = authenticated_client.get("/search/?query=marshmallows")

    assert "Camp news" in response.content.decode()
