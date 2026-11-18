from playwright.sync_api import expect
from pytest_bdd import parsers, scenarios, then, when

scenarios("pages/news_index_page.feature")


def _item(page, title):
    return page.locator("main .card").filter(has=page.get_by_role("heading", name=title, exact=True))


# --- Actions ------------------------------------------------------------------------------------------------------


@when(parsers.parse('I open the news index item "{title}"'))
def _open_item(page, title):
    _item(page, title).get_by_role("heading").get_by_role("link").click()


# --- Assertions ---------------------------------------------------------------------------------------------------


@then(parsers.parse('the news index item "{title}" shows the date "{date}", the type "{news_type}" and the text "{text}"'))
def _item_details(page, title, date, news_type, text):
    item = _item(page, title)
    expect(item).to_contain_text(date)
    expect(item).to_contain_text(news_type)
    expect(item).to_contain_text(text)


@then(parsers.parse('the news index item "{title}" is no taller than {height:d} pixels'))
def _item_height(page, title, height):
    assert _item(page, title).bounding_box()["height"] <= height
