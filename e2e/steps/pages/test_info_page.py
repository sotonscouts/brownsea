from playwright.sync_api import expect
from pytest_bdd import scenarios, then

scenarios("pages/info_page.feature")


@then("the page body reads:")
def _body(page, datatable):
    expected = [row[0] for row in datatable if row[0]]
    expect(page.locator("#main-content > *")).to_have_text(expected)
