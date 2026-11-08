from playwright.sync_api import expect
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("pages/index_page.feature")


@given(parsers.parse('the page "{title}" has the introduction "{introduction}"'))
def _introduction(scenario_state, title, introduction):
    page = scenario_state["pages"][title]
    page.introduction = introduction
    page.save()


@given(parsers.parse("index pages show {count:d} pages at a time"))
def _page_size(settings, count):
    settings.APP_SEARCH_RESULTS_PER_PAGE = count


@then("I see the child page cards:")
def _cards(page, datatable):
    titles = [row[0] for row in datatable]
    descriptions = [row[1] for row in datatable]
    expect(page.locator(".card .card-title")).to_have_text(titles)
    expect(page.locator(".card .card-text")).to_have_text(descriptions)


@then("I see no child page cards")
def _no_cards(page):
    expect(page.locator(".card")).to_have_count(0)


@when(parsers.parse('I open the card "{title}"'))
def _open_card(page, title):
    page.locator(".card").filter(has_text=title).get_by_role("link", name="Read more").click()


@when(parsers.parse('I click "{name}" in the pagination'))
def _click_pagination(page, name):
    page.get_by_label("Page navigation").get_by_role("link", name=name, exact=True).click()


@then(parsers.parse("I am on page {number:d} of the results"))
def _current_page(page, number):
    expect(page.get_by_label("Page navigation").locator(".page-item.active")).to_have_text(str(number))
