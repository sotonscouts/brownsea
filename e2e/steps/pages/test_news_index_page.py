import re

from playwright.sync_api import expect
from pytest_bdd import parsers, scenarios, then, when

scenarios("pages/news_index_page.feature")


def _item(page, title):
    return page.locator("main .card").filter(has=page.get_by_role("heading", name=title, exact=True))


# --- Actions ------------------------------------------------------------------------------------------------------


@when(parsers.parse('I open the news index item "{title}"'))
def _open_item(page, title):
    _item(page, title).get_by_role("heading").get_by_role("link").click()


@when(parsers.parse('I tick the filter "{name}"'))
def _tick(page, name):
    page.get_by_label(name, exact=True).check()


@when("I apply the filters")
def _apply(page):
    page.get_by_role("button", name="Filter", exact=True).click()


@when("I clear the filters")
def _clear(page):
    page.get_by_role("link", name="Clear filters").click()


@when("I open the filters")
def _open_filters(page):
    page.get_by_role("button", name=re.compile(r"^Filter news")).click()


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


@then(parsers.parse('the filter "{name}" is ticked'))
def _is_ticked(page, name):
    expect(page.get_by_label(name, exact=True)).to_be_checked()


@then(parsers.parse('the filter "{name}" is not ticked'))
def _is_not_ticked(page, name):
    expect(page.get_by_label(name, exact=True)).not_to_be_checked()


@then(parsers.parse('the filter "{name}" is hidden'))
def _is_hidden(page, name):
    expect(page.get_by_label(name, exact=True)).to_be_hidden()


@then(parsers.parse('the filter "{name}" is shown'))
def _is_shown(page, name):
    expect(page.get_by_label(name, exact=True)).to_be_visible()


@then(parsers.parse('the filter "{name}" is shown and ticked'))
def _is_shown_and_ticked(page, name):
    box = page.get_by_label(name, exact=True)
    expect(box).to_be_visible()
    expect(box).to_be_checked()


@then(parsers.parse("I see the filters button counting {count:d} active filter"))
def _filters_count(page, count):
    expect(page.get_by_role("button", name=f"Filter news ({count})")).to_be_visible()
