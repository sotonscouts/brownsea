import datetime

import pytest
from bs4 import BeautifulSoup
from django.utils import timezone

from brownsea.core.factories import AudienceFactory
from brownsea.events.factories import EventPageFactory, EventsIndexPageFactory, EventTopicFactory, EventTypeFactory
from brownsea.factories import publish


def soup(response):
    return BeautifulSoup(response.content, "html.parser")


def titles(response):
    return [a.get_text(strip=True) for a in soup(response).select(".event-row h3 a")]


def months(response):
    return [h.get_text(strip=True) for h in soup(response).select(".event-month")]


def days_from_now(days):
    return timezone.localdate() + datetime.timedelta(days=days)


@pytest.fixture
def events_index(site_tree):
    return publish(EventsIndexPageFactory(parent=site_tree["home"]))


def event(events_index, title, days=7, **kwargs):
    kwargs.setdefault("start_date", days_from_now(days))
    page = EventPageFactory(parent=events_index, title=title, slug=title.lower().replace(" ", "-"), **kwargs)
    return publish(page) if page.live else page


def test_shows_its_introduction(authenticated_client, events_index):
    events_index.introduction = "Everything that is coming up"
    events_index.save()

    assert soup(authenticated_client.get(events_index.url)).select_one(".lead").get_text(strip=True) == (
        "Everything that is coming up"
    )


def test_lists_upcoming_events_soonest_first_with_a_link(authenticated_client, events_index):
    later = event(events_index, "Later", days=30)
    sooner = event(events_index, "Sooner", days=3)

    response = authenticated_client.get(events_index.url)

    assert titles(response) == ["Sooner", "Later"]
    assert [a["href"] for a in soup(response).select(".event-row h3 a")] == [sooner.url, later.url]


def test_events_on_the_same_day_are_ordered_by_start_time(authenticated_client, events_index):
    event(events_index, "Evening", days=3, start_time=datetime.time(19, 0))
    event(events_index, "Morning", days=3, start_time=datetime.time(9, 0))
    event(events_index, "All day", days=3)

    assert titles(authenticated_client.get(events_index.url)) == ["All day", "Morning", "Evening"]


def test_upcoming_leaves_out_past_unpublished_and_hidden_events(authenticated_client, events_index):
    event(events_index, "Coming up", days=2)
    event(events_index, "Finished", days=-2)
    event(events_index, "Draft", days=2, live=False)
    event(events_index, "Hidden", days=2, show_in_menus=False)

    assert titles(authenticated_client.get(events_index.url)) == ["Coming up"]


@pytest.mark.parametrize(
    ("start", "end", "upcoming"),
    [
        (0, None, True),  # until the end of its day
        (-1, None, False),
        (-2, 0, True),  # a multi-day event runs until its last day is over
        (-3, -1, False),
    ],
)
def test_an_event_is_upcoming_until_the_end_of_its_last_day(authenticated_client, events_index, start, end, upcoming):
    event(
        events_index,
        "Camp",
        days=start,
        end_date=None if end is None else days_from_now(end),
    )

    assert (titles(authenticated_client.get(events_index.url)) == ["Camp"]) is upcoming
    assert (titles(authenticated_client.get(f"{events_index.url}?tab=past")) == ["Camp"]) is not upcoming


def test_the_past_tab_lists_finished_events_most_recent_first(authenticated_client, events_index):
    event(events_index, "Older", days=-30)
    event(events_index, "Recent", days=-3)
    event(events_index, "Coming up", days=3)

    assert titles(authenticated_client.get(f"{events_index.url}?tab=past")) == ["Recent", "Older"]


def test_the_tabs_show_which_is_active_and_keep_the_filters(authenticated_client, events_index):
    camp = EventTypeFactory(name="Camp", slug="camp")
    event(events_index, "Camp", event_type=camp)

    html = soup(authenticated_client.get(f"{events_index.url}?type=camp&page=2"))
    upcoming, past = html.select(".nav-pills a")

    assert "active" in upcoming["class"]
    assert upcoming["href"] == "?type=camp"
    assert past["href"] == "?type=camp&tab=past"

    html = soup(authenticated_client.get(f"{events_index.url}?tab=past"))
    upcoming, past = html.select(".nav-pills a")
    assert "active" in past["class"]
    assert upcoming["href"] == "?"


def test_events_are_grouped_under_their_month(authenticated_client, events_index):
    today = timezone.localdate()
    first = today.replace(day=1) + datetime.timedelta(days=62)
    second = first + datetime.timedelta(days=40)
    event(events_index, "One", start_date=first)
    event(events_index, "Two", start_date=first)
    event(events_index, "Three", start_date=second)

    response = authenticated_client.get(events_index.url)

    assert months(response) == [first.strftime("%B %Y"), second.strftime("%B %Y")]
    groups = soup(response).select(".event-list")
    assert [len(group.select(".event-row")) for group in groups] == [2, 1]


def test_a_row_shows_the_date_time_place_audiences_and_type(authenticated_client, events_index):
    event(
        events_index,
        "Safeguarding",
        start_date=datetime.date(2099, 11, 17),
        start_time=datetime.time(19, 30),
        end_time=datetime.time(21, 0),
        location="Online",
        event_type=EventTypeFactory(name="Training", slug="training"),
        audiences=[AudienceFactory(name="Volunteers", slug="volunteers")],
    )

    row = soup(authenticated_client.get(events_index.url)).select_one(".event-row")

    assert row.select_one(".date-tile").get_text(" ", strip=True) == "Nov 17 Tue"
    assert "Tuesday 17 November 2099, 19:30 to 21:00" in row.select_one(".event-row__meta").get_text(" ", strip=True)
    assert "Online" in row.select_one(".event-row__meta").get_text()
    badges = {badge["href"]: badge.get_text(" ", strip=True) for badge in row.select("a.badge")}
    assert badges == {
        f"{events_index.url}?audience=volunteers": "Audience: Volunteers",
        f"{events_index.url}?type=training": "Type: Training",
    }


def test_a_row_shows_three_audiences_and_counts_the_rest(authenticated_client, events_index):
    audiences = [AudienceFactory(name=f"Audience {n}", slug=f"audience-{n}") for n in range(5)]
    event(events_index, "Big", audiences=audiences)

    row = soup(authenticated_client.get(events_index.url)).select_one(".event-row")

    assert len(row.select("a.badge.text-bg-primary")) == 3
    assert row.select_one(".badge.text-bg-light").get_text(strip=True) == "+2"


def test_says_when_there_are_no_events(authenticated_client, events_index):
    assert "There are no upcoming events." in authenticated_client.get(events_index.url).content.decode()
    assert "There are no past events." in authenticated_client.get(f"{events_index.url}?tab=past").content.decode()


# Filters


@pytest.fixture
def facets(events_index):
    camp = EventTypeFactory(name="Camp", slug="camp")
    training = EventTypeFactory(name="Training", slug="training")
    cubs = AudienceFactory(name="Cubs", slug="cubs")
    volunteers = AudienceFactory(name="Volunteers", slug="volunteers")
    outdoors = EventTopicFactory(name="Outdoors", slug="outdoors")
    event(events_index, "Cub camp", days=1, event_type=camp, audiences=[cubs], topics=[outdoors])
    event(events_index, "Leader camp", days=2, event_type=camp, audiences=[volunteers])
    event(events_index, "Refresher", days=3, event_type=training, audiences=[volunteers])
    return events_index


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("type=training", ["Refresher"]),
        ("audience=cubs", ["Cub camp"]),
        ("topic=outdoors", ["Cub camp"]),
        ("type=camp&type=training", ["Cub camp", "Leader camp", "Refresher"]),  # alternatives within a facet
        ("type=camp&audience=volunteers", ["Leader camp"]),  # facets combine
        ("type=camp&audience=volunteers&topic=outdoors", []),
        ("type=nonsense", ["Cub camp", "Leader camp", "Refresher"]),  # unknown values are ignored
    ],
)
def test_filters_by_each_facet(authenticated_client, facets, query, expected):
    assert titles(authenticated_client.get(f"{facets.url}?{query}")) == expected


def test_filters_apply_to_past_events_too(authenticated_client, events_index):
    camp = EventTypeFactory(name="Camp", slug="camp")
    training = EventTypeFactory(name="Training", slug="training")
    event(events_index, "Old camp", days=-5, event_type=camp)
    event(events_index, "Old course", days=-6, event_type=training)

    assert titles(authenticated_client.get(f"{events_index.url}?type=camp&tab=past")) == ["Old camp"]


def test_an_event_with_several_matching_values_is_listed_once(authenticated_client, events_index):
    cubs = AudienceFactory(name="Cubs", slug="cubs")
    scouts = AudienceFactory(name="Scouts", slug="scouts")
    event(events_index, "Joint", audiences=[cubs, scouts])

    assert titles(authenticated_client.get(f"{events_index.url}?audience=cubs&audience=scouts")) == ["Joint"]


def test_the_filter_form_ticks_the_chosen_values_and_counts_them(authenticated_client, facets):
    html = soup(authenticated_client.get(f"{facets.url}?type=camp&audience=cubs&audience=volunteers"))

    checked = {box["id"] for box in html.select("form input[type=checkbox][checked]")}
    assert checked == {"type-camp", "audience-cubs", "audience-volunteers"}
    assert html.select_one("button[data-bs-target='#event-filters']").get_text(strip=True) == "Filter events (3)"
    assert html.select_one("#event-filters.show") is not None


def test_the_filter_form_keeps_the_tab(authenticated_client, facets):
    html = soup(authenticated_client.get(f"{facets.url}?tab=past"))

    assert html.select_one("form input[type=hidden][name=tab]")["value"] == "past"
    assert soup(authenticated_client.get(facets.url)).select_one("form input[type=hidden][name=tab]") is None


def test_clear_filters_only_shows_while_filtering_and_keeps_the_tab(authenticated_client, facets):
    assert soup(authenticated_client.get(facets.url)).find("a", string="Clear filters") is None

    clear = soup(authenticated_client.get(f"{facets.url}?type=camp")).find("a", string="Clear filters")
    assert clear["href"] == facets.url
    clear = soup(authenticated_client.get(f"{facets.url}?tab=past&type=camp")).find("a", string="Clear filters")
    assert clear["href"] == f"{facets.url}?tab=past"


def test_says_when_no_events_match(authenticated_client, facets):
    response = authenticated_client.get(f"{facets.url}?type=training&audience=cubs")

    assert "No events match these filters." in response.content.decode()


def test_the_filter_form_is_left_out_when_there_is_nothing_to_filter_by(authenticated_client, events_index):
    assert soup(authenticated_client.get(events_index.url)).select_one("form[aria-label='Filter events']") is None


# Pagination


@pytest.fixture
def three_events(events_index, settings):
    settings.APP_SEARCH_RESULTS_PER_PAGE = 2
    camp = EventTypeFactory(name="Camp", slug="camp")
    for n in range(3):
        event(events_index, f"Event {n}", days=n + 1, event_type=camp)
    return events_index


def test_events_are_paginated(authenticated_client, three_events):
    assert titles(authenticated_client.get(three_events.url)) == ["Event 0", "Event 1"]
    assert titles(authenticated_client.get(f"{three_events.url}?page=2")) == ["Event 2"]


def test_bad_page_numbers_fall_back(authenticated_client, three_events):
    assert titles(authenticated_client.get(f"{three_events.url}?page=nope")) == ["Event 0", "Event 1"]
    assert titles(authenticated_client.get(f"{three_events.url}?page=99")) == ["Event 2"]


def test_pagination_keeps_the_tab_and_filters(authenticated_client, three_events):
    html = soup(authenticated_client.get(f"{three_events.url}?type=camp"))

    next_link = html.find("a", string="Next")["href"]
    assert "page=2" in next_link
    assert "type=camp" in next_link
