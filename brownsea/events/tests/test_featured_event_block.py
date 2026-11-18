import datetime

import pytest
from bs4 import BeautifulSoup
from django.utils import timezone
from wagtail_factories import ImageFactory

from brownsea.events.factories import EventPageFactory, EventsIndexPageFactory
from brownsea.factories import publish
from brownsea.landing.factories import LandingPageFactory


def soup(response):
    return BeautifulSoup(response.content, "html.parser")


def featured(authenticated_client):
    return soup(authenticated_client.get("/")).select_one(".card.overflow-hidden")


@pytest.fixture
def events_index(site_tree):
    return publish(EventsIndexPageFactory(parent=site_tree["home"]))


def feature(home, event):
    home.body = [{"type": "featured_event", "value": {"event": event.pk}}]
    home.save()


def make_event(events_index, **kwargs):
    kwargs.setdefault("title", "District Camp")
    kwargs.setdefault("start_date", timezone.localdate() + datetime.timedelta(days=30))
    return publish(EventPageFactory(parent=events_index, **kwargs))


def test_shows_the_event_with_a_link_to_it(authenticated_client, site_tree, events_index):
    event = make_event(events_index, introduction="Three days under canvas", location="Foxlease Park", is_online=False)
    feature(site_tree["home"], event)

    card = featured(authenticated_client)

    assert card.select_one("h3 a").get_text(strip=True) == "District Camp"
    assert card.select_one("h3 a")["href"] == event.url
    assert "Three days under canvas" in card.get_text()
    assert "Foxlease Park" in card.get_text()
    assert card.select_one("a.btn")["href"] == event.url


def test_shows_the_image_when_the_event_has_one(authenticated_client, site_tree, events_index):
    with_image = make_event(events_index, title="With image", image=ImageFactory())
    feature(site_tree["home"], with_image)
    card = featured(authenticated_client)
    assert card.select_one("img") is not None
    assert card.select_one(".position-relative .date-tile") is not None
    assert card.select_one(".card-body .date-tile") is None

    without_image = make_event(events_index, title="Without image")
    feature(site_tree["home"], without_image)
    card = featured(authenticated_client)
    assert card.select_one("img") is None
    assert card.select_one(".card-body .date-tile") is not None


def test_still_shows_the_event_after_it_has_ended(authenticated_client, site_tree, events_index):
    event = make_event(events_index, start_date=timezone.localdate() - datetime.timedelta(days=1))
    feature(site_tree["home"], event)

    assert featured(authenticated_client).select_one("h3 a").get_text(strip=True) == "District Camp"


def test_shows_nothing_when_the_event_is_unpublished(authenticated_client, site_tree, events_index):
    event = make_event(events_index)
    feature(site_tree["home"], event)
    event.unpublish()

    assert featured(authenticated_client) is None


def test_shows_nothing_when_no_event_is_chosen(authenticated_client, site_tree):
    home = site_tree["home"]
    home.body = [{"type": "featured_event", "value": {"event": None}}]
    home.save()

    assert featured(authenticated_client) is None


def test_can_be_featured_on_a_landing_page(authenticated_client, site_tree, events_index):
    event = make_event(events_index)
    landing = publish(LandingPageFactory(parent=site_tree["home"], title="Hub", slug="hub"))
    landing.body = [{"type": "featured_event", "value": {"event": event.pk}}]
    landing.save()

    card = soup(authenticated_client.get(landing.url)).select_one(".card.overflow-hidden")

    assert card.select_one("h3 a").get_text(strip=True) == "District Camp"


def test_the_label_defaults_to_featured_event_and_can_be_changed_or_left_out(
    authenticated_client, site_tree, events_index
):
    event = make_event(events_index)
    home = site_tree["home"]

    def label(**value):
        home.body = [{"type": "featured_event", "value": {"event": event.pk, **value}}]
        home.save()
        tag = featured(authenticated_client).select_one("p.text-uppercase")
        return tag and tag.get_text(strip=True)

    assert label() == "Featured event"
    assert label(label_text="Booking now open") == "Booking now open"
    assert label(label_text="") is None
