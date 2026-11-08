import re

from playwright.sync_api import expect
from pytest_bdd import parsers, scenarios, then

scenarios("pages/info_page.feature")


@then(parsers.parse('the browser tab is titled "{title}"'))
def _tab_title(page, title):
    expect(page).to_have_title(re.compile(re.escape(title)))


@then("the page body reads:")
def _body(page, datatable):
    expected = [row[0] for row in datatable if row[0]]
    expect(page.locator("#main-content > *")).to_have_text(expected)
