from playwright.sync_api import expect
from pytest_bdd import given, parsers, scenarios, then, when

from brownsea.core.factories import AuthorFactory
from brownsea.news.factories import ArticlePageFactory

scenarios("pages/article_page.feature")

BODY_BLOCKS = {
    "heading": lambda index, value: {f"body__{index}__heading__heading": value},
    "text": lambda index, value: {f"body__{index}__text": f"<p>{value}</p>"},
}


def _rows(datatable):
    header, *rows = datatable
    return [dict(zip(header, row, strict=True)) for row in rows]


# --- Data ---------------------------------------------------------------------------------------------------------


@given(parsers.parse('the article "{title}" is written by "{name}", the "{role}"'))
def _author(scenario_state, title, name, role):
    article = scenario_state["pages"][title]
    article.author = AuthorFactory(name=name, role=role)
    article.save()


@given(parsers.parse('the article "{title}" has the body:'))
def _body(scenario_state, title, datatable):
    fields = {}
    for index, row in enumerate(_rows(datatable)):
        fields.update(BODY_BLOCKS[row["block"]](index, row["value"]))
    article = scenario_state["pages"][title]
    article.body = ArticlePageFactory.build(**fields).body
    article.save()


# --- Actions ------------------------------------------------------------------------------------------------------


@when(parsers.parse('I click the badge "{name}"'))
def _click_badge(page, name):
    page.locator("main .badge").filter(has_text=name).click()


# --- Assertions ---------------------------------------------------------------------------------------------------


@then(parsers.parse('the article is dated "{date}" and typed "{news_type}"'))
def _date_and_type(page, date, news_type):
    details = page.locator("main .text-muted.small").first
    expect(details).to_contain_text(date)
    expect(details).to_contain_text(news_type)


@then(parsers.parse('I see the author "{name}", the "{role}"'))
def _see_author(page, name, role):
    card = page.locator("main .card")
    expect(card.get_by_role("heading", name=name)).to_be_visible()
    expect(card).to_contain_text(role)


@then("the article image is below the date and above the introduction")
def _image_between_date_and_introduction(page):
    date = page.locator("main .text-muted.small").first.bounding_box()
    image = page.locator("main img").first.bounding_box()
    introduction = page.locator("main .lead").bounding_box()
    assert date["y"] + date["height"] <= image["y"]
    assert image["y"] + image["height"] <= introduction["y"]


@then("the article image is no taller than 40% of its width")
def _image_is_cropped(page):
    image = page.locator("main img").first.bounding_box()
    assert image["height"] <= image["width"] * 0.4 + 1, image


@then("I do not see an author")
def _no_author(page):
    expect(page.locator("main .card")).to_have_count(0)


@then("the article body reads:")
def _article_body(page, datatable):
    expect(page.locator("#main-content").locator("h2, p")).to_have_text([row[0] for row in datatable])


@then("the contents list reads:")
def _contents(page, datatable):
    expect(page.locator("#page-nav a")).to_have_text([row[0] for row in datatable])
