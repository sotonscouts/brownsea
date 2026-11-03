import pytest
from wagtail.blocks import StreamBlockValidationError
from wagtail.snippets.models import get_snippet_models

from brownsea.core.blocks import LandingPageSidebarBlock
from brownsea.core.models import Audience
from brownsea.factories import publish
from brownsea.landing.factories import LandingPageFactory
from brownsea.news.models import ArticlePage, NewsIndexPage, NewsTopic, NewsType


@pytest.fixture
def taxonomy(db):
    return {
        "announcement": NewsType.objects.create(name="Announcement", slug="announcement"),
        "update": NewsType.objects.create(name="Section Update", slug="section-update"),
        "volunteers": Audience.objects.create(name="Volunteers", slug="volunteers"),
        "beavers": Audience.objects.create(name="Beavers", slug="beavers"),
        "programme": NewsTopic.objects.create(name="Programme", slug="programme"),
        "governance": NewsTopic.objects.create(name="Governance", slug="governance"),
    }


@pytest.fixture
def news_index(site_tree):
    return site_tree["home"].add_child(instance=NewsIndexPage(title="News", slug="news", introduction="News"))


def add_article(news_index, title, news_type, *, audiences=(), topics=()):
    article = ArticlePage(
        title=title,
        slug=title.lower().replace(" ", "-"),
        introduction="Intro",
        body=[],
        news_type=news_type,
    )
    article = news_index.add_child(instance=article)
    article.audiences.set(audiences)
    article.topics.set(topics)
    return publish(article)


@pytest.fixture
def articles(news_index, taxonomy):
    t = taxonomy
    return {
        "camp": add_article(
            news_index, "Camp dates", t["announcement"], audiences=[t["volunteers"]], topics=[t["programme"]]
        ),
        "beaver_news": add_article(news_index, "Beaver news", t["update"], audiences=[t["beavers"]]),
        "board": add_article(news_index, "Board minutes", t["announcement"], topics=[t["governance"]]),
        "everyone": add_article(news_index, "For everyone", t["announcement"]),
    }


def titles(recent):
    return sorted(article.title for article in recent)


def test_articles_can_have_several_audiences_and_topics(articles, taxonomy):
    camp = articles["camp"]
    camp.audiences.add(taxonomy["beavers"])
    camp.topics.add(taxonomy["governance"])
    camp.save_revision().publish()

    camp = ArticlePage.objects.get(pk=camp.pk)
    assert set(camp.audiences.all()) == {taxonomy["volunteers"], taxonomy["beavers"]}
    assert set(camp.topics.all()) == {taxonomy["programme"], taxonomy["governance"]}


def test_home_page_without_filters_lists_everything(site_tree, articles):
    assert len(site_tree["home"].specific.get_recent_news()) == 3  # capped at the three newest


def test_home_page_can_leave_out_types(site_tree, articles, taxonomy):
    home = site_tree["home"].specific
    home.news_exclude_types.set([taxonomy["update"]])

    assert "Beaver news" not in titles(home.get_recent_news())
    assert len(home.get_recent_news()) == 3


def test_programme_style_page_shows_chosen_topics_and_leaves_out_types(site_tree, articles, taxonomy, news_index):
    add_article(news_index, "Programme update", taxonomy["update"], topics=[taxonomy["programme"]])
    page = publish(LandingPageFactory(parent=site_tree["home"], title="Programme", slug="programme"))
    page.news_topics.set([taxonomy["programme"]])
    page.news_exclude_types.set([taxonomy["update"]])

    assert titles(page.get_recent_news()) == ["Camp dates"]


def test_section_hub_shows_only_section_updates_for_its_audience(site_tree, articles, taxonomy, news_index):
    add_article(news_index, "Cubs news", taxonomy["update"], audiences=[taxonomy["volunteers"]])
    page = publish(LandingPageFactory(parent=site_tree["home"], title="Beavers", slug="beavers"))
    page.news_types.set([taxonomy["update"]])
    page.news_audiences.set([taxonomy["beavers"]])

    assert titles(page.get_recent_news()) == ["Beaver news"]


def test_an_article_in_several_matching_audiences_is_listed_once(site_tree, articles, taxonomy):
    articles["camp"].audiences.add(taxonomy["beavers"])
    page = publish(LandingPageFactory(parent=site_tree["home"], title="Sections", slug="sections"))
    page.news_audiences.set([taxonomy["volunteers"], taxonomy["beavers"]])

    assert titles(page.get_recent_news()).count("Camp dates") == 1


def test_news_index_link_carries_the_included_facets(site_tree, articles, taxonomy):
    page = publish(LandingPageFactory(parent=site_tree["home"], title="Beavers", slug="beavers"))
    page.news_types.set([taxonomy["update"]])
    page.news_audiences.set([taxonomy["beavers"]])

    url = page.get_news_index_url()

    assert url.startswith("/news/?")
    assert "type=section-update" in url
    assert "audience=beavers" in url


def test_news_index_link_is_plain_without_filters(site_tree, articles):
    assert site_tree["home"].specific.get_news_index_url() == "/news/"


def test_news_index_filters_by_query_string(authenticated_client, site_tree, articles, news_index):
    response = authenticated_client.get(news_index.url, {"audience": "beavers"})

    assert [a.title for a in response.context["sub_pages"].object_list] == ["Beaver news"]
    assert response.context["is_filtered"] is True
    assert response.context["active_filter_count"] == 1


def test_news_index_ignores_unknown_values(authenticated_client, site_tree, articles, news_index):
    response = authenticated_client.get(news_index.url, {"audience": "nobody"})

    assert len(response.context["sub_pages"].object_list) == 4
    assert response.context["is_filtered"] is False


def test_news_index_only_offers_facets_that_have_values(authenticated_client, site_tree, news_index, taxonomy):
    NewsTopic.objects.all().delete()

    response = authenticated_client.get(news_index.url)

    assert [facet.param for facet in response.context["facet_filters"]] == ["type", "audience"]


def test_recent_news_block_renders_only_where_the_page_has_news(site_tree, articles, taxonomy):
    sidebar_block = LandingPageSidebarBlock()
    page = publish(LandingPageFactory(parent=site_tree["home"], title="Hub", slug="hub"))
    page.news_types.set([taxonomy["update"]])
    value = sidebar_block.to_python([{"type": "recent_news", "value": None}])

    html = sidebar_block.render(value, context={"page": page})

    assert "Beaver news" in html
    assert "Camp dates" not in html


def test_a_landing_page_can_have_a_news_sidebar_but_does_not_need_one(authenticated_client, site_tree, articles):
    plain = publish(LandingPageFactory(parent=site_tree["home"], title="Plain", slug="plain"))
    with_news = LandingPageFactory(
        parent=site_tree["home"],
        title="With news",
        slug="with-news",
        sidebar=[{"type": "recent_news", "value": None}],
    )
    publish(with_news)

    assert "Recent News" not in authenticated_client.get(plain.url).content.decode()
    assert "Recent News" in authenticated_client.get(with_news.url).content.decode()


def test_recent_news_block_is_limited_to_one(site_tree):
    block = LandingPageSidebarBlock()
    value = block.to_python([{"type": "recent_news", "value": None}, {"type": "recent_news", "value": None}])

    with pytest.raises(StreamBlockValidationError):
        block.clean(value)


def test_news_taxonomy_is_editable_as_snippets():
    assert {NewsType, Audience, NewsTopic} <= set(get_snippet_models())


def test_news_filters_are_collapsed_on_phones_until_one_is_applied(
    authenticated_client, site_tree, articles, news_index
):
    plain = authenticated_client.get(news_index.url).content.decode()
    filtered = authenticated_client.get(news_index.url, {"audience": "beavers"}).content.decode()

    assert 'id="news-filters"' in plain
    assert "collapse d-lg-block mt-3" in plain
    assert "collapse d-lg-block show mt-3" in filtered
    assert "Filter news (1)" in filtered


def test_article_page_shows_audiences_and_topics_as_links_to_the_filtered_index(
    authenticated_client, site_tree, articles
):
    html = authenticated_client.get(articles["camp"].url).content.decode()

    assert 'href="/news/?audience=volunteers"' in html
    assert 'href="/news/?topic=programme"' in html
    assert "Volunteers" in html


def test_article_page_without_audiences_or_topics_has_no_badge_list(authenticated_client, site_tree, articles):
    html = authenticated_client.get(articles["everyone"].url).content.decode()

    assert "badge" not in html
