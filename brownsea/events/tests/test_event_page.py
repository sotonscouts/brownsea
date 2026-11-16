import datetime
import json

import pytest
from bs4 import BeautifulSoup
from django.core.exceptions import ValidationError
from django.utils import timezone

from brownsea.core.factories import AudienceFactory
from brownsea.events.factories import EventPageFactory, EventsIndexPageFactory, EventTypeFactory
from brownsea.events.models import EventPage, EventsIndexPage
from brownsea.factories import InfoPageFactory, publish
from brownsea.home.models import HomePage
from brownsea.standard_pages.models import InfoPage, ProcessPage


def soup(response):
    return BeautifulSoup(response.content, "html.parser")


def stream(*blocks):
    """Raw stream data, as stored, from (type, value) pairs."""
    return json.dumps([{"type": t, "value": v, "id": f"block-{i}"} for i, (t, v) in enumerate(blocks)])


def facts(response):
    """The event details as {label: text}."""
    return {
        dt.get_text(strip=True): dt.find_next_sibling("dd").get_text(" ", strip=True)
        for dt in soup(response).select("#event-details-heading ~ * dt, section.card dt")
    }


@pytest.fixture
def events_index(site_tree):
    return publish(EventsIndexPageFactory(parent=site_tree["home"]))


def event(events_index, **kwargs):
    kwargs.setdefault("title", "Safeguarding Refresher")
    kwargs.setdefault("slug", kwargs["title"].lower().replace(" ", "-"))
    return publish(EventPageFactory(parent=events_index, **kwargs))


# Placement


def test_events_index_only_goes_under_home_and_there_is_one():
    assert EventsIndexPage.parent_page_types == ["home.HomePage"]
    assert EventsIndexPage.max_count == 1
    assert EventsIndexPage in HomePage.allowed_subpage_models()
    assert EventsIndexPage.allowed_subpage_models() == [EventPage]


def test_events_only_go_under_the_events_index_and_hold_info_and_process_pages():
    assert EventPage.allowed_parent_page_models() == [EventsIndexPage]
    assert set(EventPage.allowed_subpage_models()) == {InfoPage, ProcessPage}
    assert EventPage in InfoPage.allowed_parent_page_models()
    assert EventPage in ProcessPage.allowed_parent_page_models()


# Validation


def test_end_date_cannot_be_before_the_start():
    page = EventPage(start_date=datetime.date(2027, 4, 30), end_date=datetime.date(2027, 4, 29))

    with pytest.raises(ValidationError) as error:
        page.clean()

    assert "end_date" in error.value.message_dict


def test_a_time_range_needs_a_start_time():
    page = EventPage(start_date=datetime.date(2027, 4, 30), end_time=datetime.time(21, 0))

    with pytest.raises(ValidationError) as error:
        page.clean()

    assert "end_time" in error.value.message_dict


def test_a_single_day_event_must_end_after_it_starts():
    page = EventPage(
        start_date=datetime.date(2027, 4, 30), start_time=datetime.time(21, 0), end_time=datetime.time(19, 0)
    )

    with pytest.raises(ValidationError) as error:
        page.clean()

    assert "end_time" in error.value.message_dict


def test_a_later_end_time_on_a_later_day_is_valid():
    page = EventPage(
        start_date=datetime.date(2027, 4, 30),
        end_date=datetime.date(2027, 5, 3),
        start_time=datetime.time(18, 0),
        end_time=datetime.time(14, 0),
    )

    page.clean()


# Upcoming


@pytest.mark.parametrize(
    ("start_offset", "end_offset", "upcoming"),
    [
        (1, None, True),
        (0, None, True),  # until the end of its last day
        (-1, None, False),
        (-2, 0, True),  # a multi-day event is upcoming until its last day is over
        (-3, -1, False),
    ],
)
def test_upcoming_until_the_end_of_the_last_day(start_offset, end_offset, upcoming):
    today = timezone.localdate()
    page = EventPage(
        start_date=today + datetime.timedelta(days=start_offset),
        end_date=None if end_offset is None else today + datetime.timedelta(days=end_offset),
    )

    assert page.is_upcoming is upcoming
    assert page.has_ended is not upcoming


def test_starts_on_combines_the_date_and_time():
    timed = EventPage(start_date=datetime.date(2027, 4, 30), start_time=datetime.time(19, 30))
    all_day = EventPage(start_date=datetime.date(2027, 4, 30))

    assert timed.starts_on == datetime.datetime(2027, 4, 30, 19, 30, tzinfo=timezone.get_current_timezone())
    assert all_day.starts_on == datetime.datetime(2027, 4, 30, 0, 0, tzinfo=timezone.get_current_timezone())


# Display


@pytest.mark.parametrize(
    ("fields", "lines"),
    [
        ({"start_date": datetime.date(2026, 11, 17)}, ["Tuesday 17 November 2026"]),
        (
            {"start_date": datetime.date(2026, 11, 17), "start_time": datetime.time(19, 30)},
            ["Tuesday 17 November 2026", "From 19:30"],
        ),
        (
            {
                "start_date": datetime.date(2026, 11, 17),
                "start_time": datetime.time(19, 30),
                "end_time": datetime.time(21, 0),
            },
            ["Tuesday 17 November 2026", "19:30 to 21:00"],
        ),
        (
            {"start_date": datetime.date(2027, 4, 30), "end_date": datetime.date(2027, 5, 3)},
            ["30 April to 3 May 2027"],
        ),
        (
            {"start_date": datetime.date(2027, 5, 1), "end_date": datetime.date(2027, 5, 3)},
            ["1 to 3 May 2027"],
        ),
        (
            {"start_date": datetime.date(2026, 12, 30), "end_date": datetime.date(2027, 1, 2)},
            ["30 December 2026 to 2 January 2027"],
        ),
        (
            {
                "start_date": datetime.date(2027, 4, 30),
                "end_date": datetime.date(2027, 5, 3),
                "start_time": datetime.time(18, 0),
                "end_time": datetime.time(14, 0),
            },
            ["30 April to 3 May 2027", "Starts 18:00, ends 14:00"],
        ),
        (
            {"start_date": datetime.date(2026, 11, 17), "end_date": datetime.date(2026, 11, 17)},
            ["Tuesday 17 November 2026"],
        ),
    ],
)
def test_when_lines(fields, lines):
    assert EventPage(**fields).when_lines == lines


@pytest.mark.parametrize(
    ("cost", "display"),
    [
        (None, None),
        ("0", "Free"),
        ("0.00", "Free"),
        ("12.5", "£12.50"),
        ("12.50", "£12.50"),
        ("100", "£100.00"),
    ],
)
def test_cost_display(cost, display):
    page = EventPage()
    page.cost = stream(*([("fixed_cost", cost)] if cost is not None else []))

    assert page.cost_display == display


# Layout


def test_a_simple_event_shows_the_details_full_width_with_no_sidebar(authenticated_client, events_index):
    page = event(events_index, body=[])

    html = soup(authenticated_client.get(page.url))

    assert html.select_one(".event-layout") is None
    assert html.select_one(".lead").get_text(strip=True) == "About this event"
    assert html.select_one("main section.card dl.row-cols-md-3") is not None


def test_an_event_with_body_content_puts_the_details_in_the_sidebar(authenticated_client, events_index):
    page = event(events_index, body__0__text="<p>Welcome</p>")

    html = soup(authenticated_client.get(page.url))

    layout = html.select_one(".event-layout")
    assert layout is not None
    assert layout.select_one(".event-layout__facts section.card") is not None
    assert layout.select_one(".event-layout__body").get_text(" ", strip=True).endswith("Welcome")
    assert layout.select_one("dl.row-cols-md-3") is None


def test_an_event_with_only_sidebar_blocks_uses_the_sidebar_layout(authenticated_client, events_index):
    page = event(events_index)
    page.sidebar = stream(
        ("key_dates", {"heading": "Key dates", "dates": [{"when": "1st April", "what": "Forms due"}]})
    )
    publish(page)

    html = soup(authenticated_client.get(page.url))

    assert html.select_one(".event-layout") is not None
    assert "Forms due" in html.select_one(".event-layout__sidebar").get_text()


def test_details_come_before_the_body_in_the_page(authenticated_client, events_index):
    page = event(events_index, body__0__text="<p>Welcome</p>")

    content = authenticated_client.get(page.url).content.decode()

    assert content.index("Event details") < content.index("Welcome")


def test_key_dates_render_the_heading_and_each_row(authenticated_client, events_index):
    page = event(events_index)
    page.sidebar = stream(
        (
            "key_dates",
            {
                "heading": "Deadlines",
                "dates": [
                    {"when": "29th April 2027 Evening", "what": "Early Tent Setup"},
                    {"when": "30th April to 3rd May 2027", "what": "District Camp"},
                ],
            },
        )
    )
    publish(page)

    sidebar = soup(authenticated_client.get(page.url)).select_one(".event-layout__sidebar")

    assert sidebar.select_one(".card-header").get_text(strip=True) == "Deadlines"
    assert [item.get_text(" ", strip=True) for item in sidebar.select("li")] == [
        "29th April 2027 Evening Early Tent Setup",
        "30th April to 3rd May 2027 District Camp",
    ]


# Details


def test_details_show_when_where_audience_type_and_cost(authenticated_client, events_index):
    volunteers = AudienceFactory(name="Volunteers", slug="volunteers")
    training = EventTypeFactory(name="Training", slug="training")
    page = event(
        events_index,
        start_date=datetime.date(2026, 11, 17),
        start_time=datetime.time(19, 30),
        end_time=datetime.time(21, 0),
        location="Online",
        event_type=training,
        audiences=[volunteers],
    )
    page.cost = stream(("fixed_cost", "0"))
    publish(page)

    details = facts(authenticated_client.get(page.url))

    assert details == {
        "When": "Tuesday 17 November 2026 19:30 to 21:00",
        "Where": "Online",
        "Who it's for": "Volunteers",
        "Type": "Training",
        "Cost": "Free",
    }


def test_audience_and_type_link_to_the_filtered_listing(authenticated_client, events_index):
    volunteers = AudienceFactory(name="Volunteers", slug="volunteers")
    training = EventTypeFactory(name="Training", slug="training")
    page = event(events_index, event_type=training, audiences=[volunteers])

    html = soup(authenticated_client.get(page.url))

    hrefs = [a["href"] for a in html.select("main section.card dd a")]
    assert f"{events_index.url}?audience=volunteers" in hrefs
    assert f"{events_index.url}?type=training" in hrefs


def test_rows_with_nothing_to_show_are_left_out(authenticated_client, events_index):
    page = event(events_index)

    assert list(facts(authenticated_client.get(page.url))) == ["When", "Type"]


def test_where_shows_the_venue_address_and_online_joining_details(authenticated_client, events_index):
    page = event(
        events_index,
        location="Foxlease Park",
        address="Lyndhurst Road\nAshurst\nSO40 7DY",
        is_online=True,
        online_details="Joining details are sent in advance",
    )

    where = soup(authenticated_client.get(page.url)).find("dt", string="Where").find_next_sibling("dd")

    text = where.get_text(" ", strip=True)
    for expected in ("Foxlease Park", "Lyndhurst Road", "SO40 7DY", "Online", "Joining details are sent in advance"):
        assert expected in text


def test_the_address_is_not_shown_in_listings(authenticated_client, events_index):
    event(events_index, location="Foxlease Park", address="Lyndhurst Road")

    assert "Lyndhurst Road" not in authenticated_client.get(events_index.url).content.decode()


# Sub-pages and linked pages


def test_info_and_process_pages_can_sit_under_an_event(events_index):
    page = event(events_index)

    info = publish(InfoPageFactory(parent=page, title="Code of conduct", slug="code-of-conduct"))
    process = page.add_child(instance=ProcessPage(title="Arrivals", slug="arrivals", introduction="Steps"))

    assert info.get_parent().specific == page
    assert process.get_parent().specific == page


def test_child_pages_block_lists_sub_pages_and_leaves_out_those_already_linked(authenticated_client, events_index):
    page = event(events_index)
    listed = publish(InfoPageFactory(parent=page, title="Code of conduct", slug="code-of-conduct"))
    linked = publish(InfoPageFactory(parent=page, title="Arrivals", slug="arrivals"))
    page.body = stream(
        ("child_pages", {"title": "Read more", "layout": "list", "show_introductions": True}),
        (
            "task_tiles",
            [{"type": "page", "value": {"icon": "file", "label": "Arrivals", "page": linked.id}, "id": "t"}],
        ),
    )
    publish(page)

    content = authenticated_client.get(page.url).content.decode()

    assert listed.title in content
    assert content.count("Arrivals") == 1


def test_linked_page_ids_cover_body_and_sidebar(events_index):
    page = event(events_index)
    in_body = publish(InfoPageFactory(parent=page, title="Body", slug="body"))
    in_sidebar = publish(InfoPageFactory(parent=page, title="Side", slug="side"))
    page.body = stream(
        ("task_tiles", [{"type": "page", "value": {"icon": "file", "label": "x", "page": in_body.id}, "id": "t"}])
    )
    page.sidebar = stream(
        (
            "quick_links",
            {"heading": "Useful Links", "links": [{"type": "page", "value": {"page": in_sidebar.id}, "id": "q"}]},
        )
    )

    assert page.get_linked_page_ids() == [in_body.id, in_sidebar.id]


def test_a_new_event_has_no_linked_pages(events_index):
    assert event(events_index).get_linked_page_ids() == []


# Key date links


def key_dates_sidebar(events_index, *dates):
    page = event(events_index)
    page.sidebar = stream(("key_dates", {"heading": "Key dates", "dates": list(dates)}))
    return publish(page)


def date_item(**value):
    return {"type": "item", "id": "d", "value": {"when": "18th November 2026", "what": "Info meeting", **value}}


def test_a_key_date_can_link_to_a_page(authenticated_client, events_index):
    meeting = event(events_index, title="Group Info Meeting")
    page = key_dates_sidebar(events_index, date_item(page=meeting.id))

    link = soup(authenticated_client.get(page.url)).select_one(".event-layout__sidebar li a")

    assert link["href"] == meeting.url
    assert link.get_text(strip=True) == "Info meeting"


def test_a_key_date_can_link_to_an_address(authenticated_client, events_index):
    page = key_dates_sidebar(events_index, date_item(url="https://example.org/form"))

    link = soup(authenticated_client.get(page.url)).select_one(".event-layout__sidebar li a")

    assert link["href"] == "https://example.org/form"


def test_a_chosen_page_wins_over_an_address(authenticated_client, events_index):
    meeting = event(events_index, title="Group Info Meeting")
    page = key_dates_sidebar(events_index, date_item(page=meeting.id, url="https://example.org/form"))

    links = soup(authenticated_client.get(page.url)).select(".event-layout__sidebar li a")

    assert [link["href"] for link in links] == [meeting.url]


def test_a_key_date_with_no_link_is_plain_text(authenticated_client, events_index):
    page = key_dates_sidebar(events_index, date_item())

    row = soup(authenticated_client.get(page.url)).select_one(".event-layout__sidebar li")

    assert row.select_one("a") is None
    assert row.get_text(" ", strip=True) == "18th November 2026 Info meeting"
