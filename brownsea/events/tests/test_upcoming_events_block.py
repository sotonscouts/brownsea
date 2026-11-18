import datetime

import pytest
from bs4 import BeautifulSoup
from django.utils import timezone

from brownsea.core.factories import AudienceFactory
from brownsea.events.factories import (
    EventPageFactory,
    EventsIndexPageFactory,
    EventTopicFactory,
    EventTypeFactory,
)
from brownsea.factories import publish


def soup(response):
    return BeautifulSoup(response.content, "html.parser")


@pytest.fixture
def home(site_tree):
    return site_tree["home"]


@pytest.fixture
def events_index(home):
    return publish(EventsIndexPageFactory(parent=home))


def event(events_index, title, days=7, **kwargs):
    kwargs.setdefault("start_date", timezone.localdate() + datetime.timedelta(days=days))
    return publish(EventPageFactory(parent=events_index, title=title, slug=title.lower().replace(" ", "-"), **kwargs))


def upcoming_block(**value):
    value = {"heading": "Upcoming events", "types": [], "audiences": [], "topics": [], **value}
    return {"type": "upcoming_events", "value": value}


def show_in_body(home, **value):
    home.body = [upcoming_block(**value)]
    home.save()


def show_in_sidebar(home, **value):
    home.sidebar = [upcoming_block(**value)]
    home.save()


def card_titles(response):
    return [a.get_text(strip=True) for a in soup(response).select("main .card h3 a")]


def test_lists_the_next_four_upcoming_events_soonest_first(authenticated_client, home, events_index):
    for days in (5, 1, 3, 2, 4):
        event(events_index, f"In {days}", days=days)
    event(events_index, "Finished", days=-3)
    show_in_body(home, layout="cards")

    assert card_titles(authenticated_client.get("/")) == ["In 1", "In 2", "In 3", "In 4"]


def test_shows_the_heading_and_links_to_each_event_and_the_index(authenticated_client, home, events_index):
    camp = event(events_index, "Camp")
    show_in_body(home, heading="What's on", layout="cards")

    page = soup(authenticated_client.get("/"))

    assert page.select_one("main h2.h4").get_text(strip=True) == "What's on"
    assert page.select_one("main .card h3 a")["href"] == camp.url
    assert page.find("a", string=lambda text: text and "View all events" in text)["href"] == events_index.url


def test_a_blank_heading_is_left_out(authenticated_client, home, events_index):
    event(events_index, "Camp")
    show_in_body(home, heading="", layout="cards")

    assert soup(authenticated_client.get("/")).select_one("main h2.h4") is None


def test_the_list_layout_is_one_compact_card(authenticated_client, home, events_index):
    event(events_index, "Camp")
    event(events_index, "Social", days=9)
    show_in_body(home, layout="list")

    page = soup(authenticated_client.get("/"))

    assert [h.get_text(strip=True) for h in page.select("main .list-group-item h3")] == ["Camp", "Social"]
    assert page.select_one("main .card-header h2").get_text(strip=True) == "Upcoming events"


def test_the_sidebar_block_is_a_compact_list(authenticated_client, home, events_index):
    event(events_index, "Camp")
    show_in_sidebar(home)

    page = soup(authenticated_client.get("/"))

    assert [h.get_text(strip=True) for h in page.select("main .list-group-item h3")] == ["Camp"]


def test_the_block_narrows_by_each_facet_and_the_view_all_link_carries_them(authenticated_client, home, events_index):
    camp, social = EventTypeFactory(name="Camp", slug="camp"), EventTypeFactory(name="Social", slug="social")
    cubs, beavers = AudienceFactory(name="Cubs", slug="cubs"), AudienceFactory(name="Beavers", slug="beavers")
    sailing = EventTopicFactory(name="Sailing", slug="sailing")
    event(events_index, "Cub camp", event_type=camp, audiences=[cubs], topics=[sailing])
    event(events_index, "Cub social", event_type=social, audiences=[cubs])
    event(events_index, "Beaver camp", event_type=camp, audiences=[beavers])
    show_in_body(home, types=[camp.pk], audiences=[cubs.pk], topics=[sailing.pk], layout="cards")

    response = authenticated_client.get("/")

    assert card_titles(response) == ["Cub camp"]
    view_all = soup(response).find("a", string=lambda text: text and "View all events" in text)["href"]
    assert view_all == f"{events_index.url}?type=camp&audience=cubs&topic=sailing"


def test_shows_nothing_when_no_events_are_coming_up(authenticated_client, home, events_index):
    event(events_index, "Finished", days=-3)
    show_in_body(home, layout="cards")

    page = soup(authenticated_client.get("/"))

    assert page.select_one("main .card") is None
    assert "Upcoming events" not in page.get_text()


def test_shows_nothing_when_the_site_has_no_events_index(authenticated_client, home):
    show_in_body(home, layout="cards")

    assert "Upcoming events" not in soup(authenticated_client.get("/")).get_text()


def test_can_be_used_on_a_landing_page(authenticated_client, home, events_index):
    from brownsea.landing.factories import LandingPageFactory

    event(events_index, "Camp")
    landing = publish(LandingPageFactory(parent=home, title="Hub", slug="hub"))
    landing.body = [upcoming_block(layout="cards")]
    landing.sidebar = [upcoming_block()]
    landing.save()

    page = soup(authenticated_client.get(landing.url))

    assert page.select_one("main .row-cols-md-2 .card h3 a").get_text(strip=True) == "Camp"
    assert page.select_one("main .list-group-item h3 a").get_text(strip=True) == "Camp"


@pytest.mark.parametrize("sidebar", ["home", "landing"])
def test_the_sidebar_allows_only_one_upcoming_events_block(home, sidebar):
    from wagtail.blocks import StreamBlockValidationError

    from brownsea.core.blocks import HomePageSidebarBlock, LandingPageSidebarBlock

    block = {"home": HomePageSidebarBlock, "landing": LandingPageSidebarBlock}[sidebar]()
    one = [upcoming_block()]

    block.clean(block.to_python(one))
    with pytest.raises(StreamBlockValidationError):
        block.clean(block.to_python(one * 2))


@pytest.mark.parametrize("block_class", ["UpcomingEventsBlock", "UpcomingEventsSidebarBlock"])
def test_a_new_block_starts_with_no_filters(block_class):
    from brownsea.core import blocks

    default = getattr(blocks, block_class)().get_default()

    assert [len(default[facet]) for facet in ("types", "audiences", "topics")] == [0, 0, 0]
