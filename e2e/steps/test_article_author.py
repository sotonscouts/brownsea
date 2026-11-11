from playwright.sync_api import expect
from pytest_bdd import parsers, scenarios, then, when

scenarios("editing/article_author.feature")


def _chooser(page):
    return page.get_by_role("dialog")


@when(parsers.parse('I edit the article "{title}"'))
def _edit_article(page, scenario_state, title):
    page.goto(f"/admin/pages/{scenario_state['pages'][title].pk}/edit/")


@when("I open the author chooser")
def _open_chooser(page):
    page.get_by_role("button", name="Choose an author").click()
    expect(_chooser(page)).to_be_visible()


@when(parsers.parse('I choose the author "{label}" by searching for "{query}"'))
def _choose_author(page, label, query):
    _open_chooser(page)
    _chooser(page).locator("input[name=q]").fill(query)
    _chooser(page).get_by_role("link", name=label).click()


@then(parsers.parse('the author field shows "{label}"'))
def _author_field(page, label):
    expect(page.locator("#id_author_role-title")).to_have_text(label)


@then("I am not offered to create a new role")
def _no_create(page):
    expect(_chooser(page).get_by_role("tab", name="Create")).to_have_count(0)
