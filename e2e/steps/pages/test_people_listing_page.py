import re

from playwright.sync_api import expect
from pytest_bdd import given, parsers, scenarios, then

from brownsea.people.factories import PersonFactory, PersonListingPageFactory, PersonRoleFactory, PersonTeamFactory

scenarios("pages/people_listing_page.feature")


def _rows(datatable):
    header, *rows = datatable
    return [dict(zip(header, row, strict=True)) for row in rows]


def _section(page, heading):
    return page.locator("main section").filter(has=page.get_by_role("heading", name=heading, exact=True))


@given("the site has a people page")
def _people_page(scenario_state):
    scenario_state["pages"]["People"] = PersonListingPageFactory(parent=scenario_state["home"])


@given("the people are:")
def _people(datatable):
    """
    Columns: name, in listing (yes or no), and roles: `Title @ Team` entries separated by `;`.

    Follow an entry with `[past]` for a past role, or `[priority 10]` to rank it within its team.
    """
    teams = {}
    for row in _rows(datatable):
        person = PersonFactory(name=row["name"], show_in_listing=row["in listing"] == "yes")
        for entry in row["roles"].split(";"):
            title, _, team = entry.strip().partition(" @ ")
            is_current = "[past]" not in team
            priority = int(match.group(1)) if (match := re.search(r"\[priority (\d+)\]", team)) else 0
            team = re.sub(r"\[.*?\]", "", team).strip()
            if team and team not in teams:
                teams[team] = PersonTeamFactory(name=team)
            PersonRoleFactory(
                person=person, title=title.strip(), team=teams.get(team), is_current=is_current, priority=priority
            )


@then(parsers.parse('the people page has the team sections "{headings}"'))
def _team_sections(page, headings):
    expect(page.locator("main section h2")).to_have_text(headings.split(", "))


@then(parsers.parse('I see the "{heading}" section lists:'))
def _section_lists(page, heading, datatable):
    cards = _section(page, heading).locator(".card")
    rows = _rows(datatable)
    expect(cards).to_have_count(len(rows))
    for card, row in zip(cards.all(), rows, strict=True):
        expect(card.get_by_role("heading")).to_have_text(row["name"])
        expect(card).to_contain_text(row["roles"])
