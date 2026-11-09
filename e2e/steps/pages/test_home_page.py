from django.utils.text import slugify
from playwright.sync_api import expect
from pytest_bdd import given, parsers, scenarios, then, when

from brownsea.core.factories import AudienceFactory
from brownsea.news.factories import NewsTopicFactory, NewsTypeFactory

scenarios("pages/home_page.feature")

FACETS = {"type": "news_types", "topic": "news_topics", "audience": "news_audiences"}


def _recent_news(page):
    return page.locator(".card").filter(has=page.get_by_role("heading", name="Recent News"))


def _recent_news_item(page, title):
    return _recent_news(page).locator(".list-group-item").filter(has=page.get_by_role("heading", name=title))


# --- Data ---------------------------------------------------------------------------------------------------------


@given(parsers.parse('the home page has the introduction "{introduction}"'))
def _introduction(scenario_state, introduction):
    home = scenario_state["home"]
    home.introduction = introduction
    home.save()


@given(parsers.parse('the home page only shows news with the {facet:w} "{name}"'))
def _news_filter(scenario_state, facet, name):
    factory = {"type": NewsTypeFactory, "topic": NewsTopicFactory, "audience": AudienceFactory}[facet]
    home = scenario_state["home"]
    getattr(home, FACETS[facet]).add(factory(name=name, slug=slugify(name)))
    home.save()


# --- Actions ------------------------------------------------------------------------------------------------------


@when(parsers.parse('I search for "{query}" using the home page search form'))
def _search_from_home(page, query):
    box = page.locator("main").get_by_role("searchbox")
    box.fill(query)
    box.press("Enter")


@when(parsers.parse('I open the recent news item "{title}"'))
def _open_recent_news_item(page, title):
    _recent_news_item(page, title).get_by_role("heading").get_by_role("link").click()


# --- Assertions ---------------------------------------------------------------------------------------------------


@then("the recent news is:")
def _recent_news_is(page, datatable):
    expect(_recent_news(page).locator(".list-group-item h3")).to_have_text([row[0] for row in datatable])


@then("there is no recent news")
def _no_recent_news(page):
    expect(_recent_news(page)).to_have_count(0)


@then(parsers.parse('the recent news item "{title}" shows the date "{date}" and the type "{news_type}"'))
def _item_date_and_type(page, title, date, news_type):
    item = _recent_news_item(page, title)
    expect(item).to_contain_text(date)
    expect(item).to_contain_text(news_type)


@then(parsers.parse('the recent news item "{title}" shows its image and the introduction "{introduction}"'))
def _item_featured(page, title, introduction):
    item = _recent_news_item(page, title)
    expect(item.locator("img")).to_be_visible()
    expect(item).to_contain_text(introduction)


@then(parsers.parse('the recent news item "{title}" shows no image or introduction'))
def _item_plain(page, title):
    item = _recent_news_item(page, title)
    expect(item.locator("img")).to_have_count(0)
    expect(item.locator("p")).to_have_count(1)  # just the date and type
