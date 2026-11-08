from playwright.sync_api import expect
from pytest_bdd import parsers, scenarios, then, when

scenarios("in_page_navigation.feature")


@when(parsers.parse('I click "{name}" in the page navigation'))
def _click_in_page_nav(page, name):
    page.locator("#page-nav").get_by_role("link", name=name, exact=True).click()


@then(parsers.parse('the heading "{text}" is in view'))
def _in_view(page, text):
    expect(page.get_by_role("heading", name=text, level=2)).to_be_in_viewport()
