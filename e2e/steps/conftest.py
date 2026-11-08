"""Steps shared by every feature."""

import re

import pytest
from playwright.sync_api import expect
from pytest_bdd import given, parsers, then, when

from brownsea.factories import IndexPageFactory, InfoPageFactory, UserFactory
from brownsea.navigation.factories import NavigationSettingsFactory, nav_link


def _link(scope, name):
    """A link by its visible text. Icon glyphs in the link are part of its accessible name, so allow for them."""
    return scope.get_by_role("link", name=re.compile(rf"^\W*{re.escape(name)}$"))


def _page(state, title):
    return state["pages"][title]


@pytest.fixture
def scenario_state():
    """Scratch space for sharing values between the steps of a scenario."""
    return {"pages": {}}


# --- Data ---------------------------------------------------------------------------------------------------------


@given("the intranet has a site")
def _site(make_site, scenario_state):
    site, home = make_site()
    scenario_state.update(site=site, home=home)
    scenario_state["pages"]["Home"] = home


@given("the home page is public")
def _public_home(scenario_state):
    home = scenario_state["home"]
    home.access_level = "public"
    home.save()


@given("I am logged in")
def _logged_in(log_in):
    log_in(UserFactory())


@given(parsers.parse('the page "{parent}" has an info page "{title}"'))
@given(parsers.parse('the site has an info page "{title}"'))
def _info_page(scenario_state, title, parent="Home"):
    scenario_state["pages"][title] = InfoPageFactory(parent=_page(scenario_state, parent), title=title)


@given(parsers.parse('the page "{parent}" has an info page "{title}" with the introduction "{introduction}"'))
@given(parsers.parse('the site has an info page "{title}" with the introduction "{introduction}"'))
def _info_page_with_introduction(scenario_state, title, introduction, parent="Home"):
    scenario_state["pages"][title] = InfoPageFactory(
        parent=_page(scenario_state, parent), title=title, introduction=introduction
    )


@given(parsers.parse('the page "{parent}" has an index page "{title}"'))
@given(parsers.parse('the site has an index page "{title}"'))
def _index_page(scenario_state, title, parent="Home"):
    scenario_state["pages"][title] = IndexPageFactory(parent=_page(scenario_state, parent), title=title)


@given(parsers.parse('the site has an info page "{title}" with the headings:'))
def _info_page_with_headings(scenario_state, title, datatable):
    headings = {f"body__{index}__heading__heading": row[0] for index, row in enumerate(datatable)}
    scenario_state["pages"][title] = InfoPageFactory(parent=scenario_state["home"], title=title, **headings)


@given("the navigation has the links:")
def _navigation_links(scenario_state, datatable):
    _, *rows = datatable  # first row is the header: title | page | url
    items = [
        nav_link(title=title, page=_page(scenario_state, page) if page else None, url=url) for title, page, url in rows
    ]
    NavigationSettingsFactory(site=scenario_state["site"], primary_navigation=items)


@given(parsers.parse('the navigation has a "{title}" menu with the group "{heading}" containing the pages:'))
def _navigation_menu(scenario_state, title, heading, datatable):
    pages = [_page(scenario_state, row[0]) for row in datatable]
    NavigationSettingsFactory(
        site=scenario_state["site"], primary_navigation=[nav_link(title=title, groups={heading: pages})]
    )


@given("anonymous visitors can see the menu")
def _menu_for_anonymous(settings):
    settings.APP_SHOW_MENU_WHEN_UNAUTHENTICATED = True


# --- Actions ------------------------------------------------------------------------------------------------------


@when(parsers.parse('I visit "{path}"'))
def _visit(page, scenario_state, path):
    scenario_state["response"] = page.goto(path)


@when(parsers.parse('I click "{name}" in the navigation'))
def _click_in_navigation(page, name):
    _link(page.locator("nav.navbar"), name).click()


@when(parsers.parse('I click "{name}" in the breadcrumbs'))
def _click_in_breadcrumbs(page, name):
    page.get_by_label("breadcrumb").get_by_role("link", name=name, exact=True).click()


@when(parsers.parse('I click "{name}" in the menu'))
def _click_in_menu(page, name):
    page.locator(".dropdown-menu.show").get_by_role("link", name=name, exact=True).click()


# --- Assertions ---------------------------------------------------------------------------------------------------


@then(parsers.parse("the response status is {status:d}"))
def _status(scenario_state, status):
    assert scenario_state["response"].status == status


@then(parsers.parse('I see the heading "{text}"'))
def _heading(page, text):
    expect(page.get_by_role("heading", name=text, level=1)).to_be_visible()


@then(parsers.parse('I see the text "{text}"'))
def _text(page, text):
    expect(page.get_by_text(text).first).to_be_visible()


@then(parsers.parse('I do not see the text "{text}"'))
def _no_text(page, text):
    expect(page.get_by_text(text)).to_have_count(0)


@then(parsers.parse('I am on "{path}"'))
def _on_path(page, base_url, path):
    expect(page).to_have_url(f"{base_url}{path}")


@then(parsers.parse('I see "{name}" in the navigation'))
def _see_in_navigation(page, name):
    expect(_link(page.locator("nav.navbar"), name)).to_be_visible()


@then(parsers.parse('I do not see "{name}" in the navigation'))
def _not_in_navigation(page, name):
    expect(_link(page.locator("nav.navbar"), name)).to_have_count(0)


@then(parsers.parse('I see the "{name}" button in the navigation'))
def _button_in_navigation(page, name):
    # The logout button is icon-only, so it is found by its title.
    expect(page.locator("nav.navbar").get_by_title(name)).to_be_visible()


@then(parsers.parse('the breadcrumbs are "{trail}"'))
def _breadcrumbs(page, trail):
    links = page.get_by_label("breadcrumb").get_by_role("link")
    expect(links).to_have_text(trail.split(" > "))


@then("there are no breadcrumbs")
def _no_breadcrumbs(page):
    expect(page.get_by_label("breadcrumb")).to_have_count(0)


@then("the browser reported no errors")
def _no_browser_errors(browser_errors):
    assert browser_errors == []
