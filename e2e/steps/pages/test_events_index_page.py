from playwright.sync_api import expect
from pytest_bdd import parsers, scenarios, then, when

scenarios("pages/events_index_page.feature")


def _item(page, title):
    return page.locator("main .event-row").filter(has=page.get_by_role("heading", name=title, exact=True))


# --- Actions ------------------------------------------------------------------------------------------------------


@when(parsers.parse('I open the events index item "{title}"'))
def _open_item(page, title):
    _item(page, title).get_by_role("heading").get_by_role("link").click()


@when(parsers.parse('I open the "{name}" tab'))
def _open_tab(page, name):
    page.locator("main .nav-pills").get_by_role("link", name=name).click()


@when(parsers.parse('I click the badge "{name}" on the events index item "{title}"'))
def _click_badge(page, name, title):
    _item(page, title).locator("a.badge").filter(has_text=name).click()


# --- Assertions ---------------------------------------------------------------------------------------------------


@then("the month headings read:")
def _month_headings(page, datatable):
    expect(page.locator("main .event-month")).to_have_text([row[0] for row in datatable])


@then(parsers.parse('the events index item "{title}" shows the date tile "{text}"'))
def _shows_date_tile(page, title, text):
    expect(_item(page, title).locator(".date-tile")).to_contain_text(text)


@then(parsers.parse('the events index item "{title}" shows "{text}"'))
def _shows(page, title, text):
    expect(_item(page, title)).to_contain_text(text)


@then(parsers.parse('the date tile of "{title}" is to the left of its title and has a coloured month'))
def _date_tile_layout(page, title):
    item = _item(page, title)
    tile = item.locator(".date-tile").bounding_box()
    heading = item.get_by_role("heading").bounding_box()
    assert tile["x"] + tile["width"] <= heading["x"]
    assert abs(tile["y"] - heading["y"]) < 20
    month = item.locator(".date-tile__month")
    assert month.evaluate("el => getComputedStyle(el).backgroundColor") != "rgba(0, 0, 0, 0)"
