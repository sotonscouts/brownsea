from playwright.sync_api import expect
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("not_found.feature")


@given("the intranet has a site")
def _site(make_site):
    make_site()


@when(parsers.parse('I visit "{path}"'))
def _visit(page, scenario_state, path):
    scenario_state["response"] = page.goto(path)


@then(parsers.parse("the response status is {status:d}"))
def _status(scenario_state, status):
    assert scenario_state["response"].status == status


@then(parsers.parse('I see the heading "{text}"'))
def _heading(page, text):
    expect(page.get_by_role("heading", name=text, level=1)).to_be_visible()
