import re

from playwright.sync_api import expect
from pytest_bdd import parsers, scenarios, then, when

scenarios("magic_links.feature")


def _dialog(page):
    return page.locator(".modal.show")


def _row(page, label):
    return _dialog(page).locator("[data-magic-link-row]").filter(has_text=label)


@when("I open the share dialog")
def _open_share_dialog(page):
    page.get_by_role("button", name="Share").click()
    expect(_dialog(page).get_by_text("Share magic links")).to_be_visible()


@when(parsers.parse('I create a magic link labelled "{label}"'))
def _create_magic_link(page, label):
    _dialog(page).get_by_label("Label (optional)").fill(label)
    _dialog(page).get_by_role("button", name="Create").click()
    expect(_row(page, label)).to_be_visible()


@when(parsers.parse('I revoke the magic link "{label}"'))
def _revoke_magic_link(page, label):
    _row(page, label).get_by_role("button", name="Revoke").click()


@then(parsers.parse('I see the magic link "{label}" in the share dialog'))
def _see_magic_link(page, label):
    row = _row(page, label)
    expect(row).to_be_visible()
    expect(row.locator("input[type=text]")).to_have_value(re.compile(r"\?access="))


@then(parsers.parse('I do not see the magic link "{label}" in the share dialog'))
def _no_magic_link(page, label):
    expect(_row(page, label)).to_have_count(0)


@then(parsers.parse('I do not see the "{name}" button'))
def _no_button(page, name):
    expect(page.get_by_role("button", name=name)).to_have_count(0)


@then(parsers.parse('someone who is not logged in can open the link and see the heading "{heading}"'))
def _open_link_elsewhere(page, browser, heading):
    url = page.locator("[data-magic-link-row] input[type=text]").first.input_value()

    visitor = browser.new_context()
    try:
        other = visitor.new_page()
        other.goto(url)
        expect(other.get_by_role("heading", name=heading, level=1)).to_be_visible()
    finally:
        visitor.close()
