from playwright.sync_api import expect
from pytest_bdd import parsers, scenarios, then, when

scenarios("search.feature")


@when(parsers.parse('I search for "{query}"'))
def _search(page, query):
    box = page.get_by_role("searchbox", name="Search", exact=True)
    box.fill(query)
    box.press("Enter")


@then("I see the search results:")
def _results(page, datatable):
    expect(page.locator(".list-group-item h3")).to_have_text([row[0] for row in datatable])


@when(parsers.parse('I open the search result "{title}"'))
def _open_result(page, title):
    page.locator(".list-group-item").filter(has_text=title).click()
