import pytest
from bs4 import BeautifulSoup

from brownsea.factories import publish
from brownsea.people.factories import (
    PersonFactory,
    PersonListingPageFactory,
    PersonRoleFactory,
    PersonTeamFactory,
)
from brownsea.people.models import PersonListingPage


@pytest.fixture
def listing(site_tree):
    return publish(PersonListingPageFactory(parent=site_tree["home"]))


def sections(client, listing):
    """Each section as (heading or None, [(name, [role titles])])."""
    soup = BeautifulSoup(client.get(listing.url).content, "html.parser")
    return [
        (
            heading.get_text(strip=True) if (heading := section.select_one("h2")) else None,
            [
                (
                    card.select_one(".card-title").get_text(strip=True),
                    [p.get_text(strip=True) for p in card.select("p")],
                )
                for card in section.select(".card")
            ],
        )
        for section in soup.select("main section")
    ]


def test_there_is_one_listing_page_under_the_home_page(site_tree):
    assert PersonListingPage.max_count == 1
    assert PersonListingPage.can_exist_under(site_tree["home"]) is True


def test_only_people_marked_to_show_are_listed(authenticated_client, listing):
    team = PersonTeamFactory(name="District team")
    PersonFactory(name="Shown", show_in_listing=True, role="Lead", role__team=team)
    PersonFactory(name="Hidden", show_in_listing=False, role="Lead", role__team=team)

    assert sections(authenticated_client, listing) == [("District team", [("Shown", ["Lead"])])]


def test_teams_come_in_their_set_order_and_people_in_name_order(authenticated_client, listing):
    trustees = PersonTeamFactory(name="Trustees", sort_order=2)
    district = PersonTeamFactory(name="District team", sort_order=1)
    PersonFactory(name="Zed Young", show_in_listing=True, role="Chair", role__team=trustees)
    PersonFactory(name="Alex Jones", show_in_listing=True, role="Treasurer", role__team=trustees)
    PersonFactory(name="Sam Smith", show_in_listing=True, role="District Commissioner", role__team=district)

    assert [(heading, [name for name, _ in people]) for heading, people in sections(authenticated_client, listing)] == [
        ("District team", ["Sam Smith"]),
        ("Trustees", ["Alex Jones", "Zed Young"]),
    ]


def test_higher_priority_people_come_first_then_alphabetical(authenticated_client, listing):
    team = PersonTeamFactory(name="District team")
    PersonFactory(name="Alex Jones", show_in_listing=True, role="Treasurer", role__team=team)
    PersonFactory(name="Zed Young", show_in_listing=True, role="Chair", role__team=team, role__priority=10)
    PersonFactory(name="Sam Smith", show_in_listing=True, role="Secretary", role__team=team, role__priority=5)
    PersonFactory(name="Bea Brown", show_in_listing=True, role="Member", role__team=team)

    people = sections(authenticated_client, listing)[0][1]

    assert [name for name, _ in people] == ["Zed Young", "Sam Smith", "Alex Jones", "Bea Brown"]


def test_a_person_is_ranked_by_their_highest_priority_role_in_the_team(authenticated_client, listing):
    team = PersonTeamFactory(name="District team")
    PersonFactory(name="Alex Jones", show_in_listing=True, role="Treasurer", role__team=team, role__priority=5)
    sam = PersonFactory(name="Sam Smith", show_in_listing=True, role="Member", role__team=team)
    PersonRoleFactory(person=sam, title="Chair", team=team, priority=9)

    people = sections(authenticated_client, listing)[0][1]

    assert [name for name, _ in people] == ["Sam Smith", "Alex Jones"]


def test_priority_in_one_team_does_not_rank_a_person_in_another(authenticated_client, listing):
    district = PersonTeamFactory(name="District team", sort_order=1)
    trustees = PersonTeamFactory(name="Trustees", sort_order=2)
    sam = PersonFactory(name="Sam Smith", show_in_listing=True, role="Member", role__team=trustees)
    PersonRoleFactory(person=sam, title="Chair", team=district, priority=9)
    PersonFactory(name="Alex Jones", show_in_listing=True, role="Treasurer", role__team=trustees, role__priority=1)

    assert [(heading, [name for name, _ in people]) for heading, people in sections(authenticated_client, listing)] == [
        ("District team", ["Sam Smith"]),
        ("Trustees", ["Alex Jones", "Sam Smith"]),
    ]


def test_someone_with_roles_in_two_teams_is_in_both_with_that_teams_role(authenticated_client, listing):
    district = PersonTeamFactory(name="District team", sort_order=1)
    trustees = PersonTeamFactory(name="Trustees", sort_order=2)
    sam = PersonFactory(name="Sam Smith", show_in_listing=True, role="District Commissioner", role__team=district)
    PersonRoleFactory(person=sam, title="Trustee", team=trustees)

    assert sections(authenticated_client, listing) == [
        ("District team", [("Sam Smith", ["District Commissioner"])]),
        ("Trustees", [("Sam Smith", ["Trustee"])]),
    ]


def test_several_roles_in_one_team_are_all_shown(authenticated_client, listing):
    team = PersonTeamFactory(name="District team")
    sam = PersonFactory(name="Sam Smith", show_in_listing=True, role="District Commissioner", role__team=team)
    PersonRoleFactory(person=sam, title="Safeguarding Lead", team=team)

    assert sections(authenticated_client, listing) == [
        ("District team", [("Sam Smith", ["District Commissioner", "Safeguarding Lead"])])
    ]


def test_past_roles_are_not_listed(authenticated_client, listing):
    team = PersonTeamFactory(name="District team")
    sam = PersonFactory(name="Sam Smith", show_in_listing=True, role="Deputy", role__team=team, role__is_current=False)
    PersonRoleFactory(person=sam, title="Trustee", team=team)

    assert sections(authenticated_client, listing) == [("District team", [("Sam Smith", ["Trustee"])])]


def test_someone_with_only_past_roles_is_listed_by_name_alone(authenticated_client, listing):
    PersonFactory(name="Sam Smith", show_in_listing=True, role="Deputy", role__is_current=False)

    assert sections(authenticated_client, listing) == [(None, [("Sam Smith", [])])]


def test_roles_with_no_team_come_last_under_other_roles(authenticated_client, listing):
    team = PersonTeamFactory(name="District team")
    PersonFactory(name="Sam Smith", show_in_listing=True, role="District Commissioner", role__team=team)
    PersonFactory(name="Taylor Brown", show_in_listing=True, role="Website editor")

    assert sections(authenticated_client, listing) == [
        ("District team", [("Sam Smith", ["District Commissioner"])]),
        ("Other roles", [("Taylor Brown", ["Website editor"])]),
    ]


def test_with_no_teams_the_people_are_one_list_without_a_heading(authenticated_client, listing):
    PersonFactory(name="Sam Smith", show_in_listing=True, role="District Commissioner")

    assert sections(authenticated_client, listing) == [(None, [("Sam Smith", ["District Commissioner"])])]


def test_it_shows_the_introduction(authenticated_client, site_tree):
    listing = publish(PersonListingPageFactory(parent=site_tree["home"], introduction="Who we are"))

    soup = BeautifulSoup(authenticated_client.get(listing.url).content, "html.parser")

    assert soup.select_one(".lead").get_text(strip=True) == "Who we are"
