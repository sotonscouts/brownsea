from urllib.parse import urlencode

from django.db import models
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.datastructures import MultiValueDict

from brownsea.core.filters import AudienceFilter, FacetFilterSet, TaxonomyFilter
from brownsea.events.models.pages import EventPage, EventsIndexPage
from brownsea.events.models.snippets import EventTopic, EventType


def _listed_events(under, *, finished):
    """Live events shown in listings that have finished or have not. An event runs to the end of its last day."""
    events = EventPage.objects.live().filter(show_in_menus=True)
    if under is not None:
        events = events.descendant_of(under)
    events = events.annotate(
        ends_on=Coalesce("end_date", "start_date", output_field=models.DateField())
    ).select_related("event_type")
    if finished:
        return events.filter(ends_on__lt=timezone.localdate()).order_by("-start_date", "-start_time", "title")
    return events.filter(ends_on__gte=timezone.localdate()).order_by("start_date", "start_time", "title")


def upcoming_events(under=None):
    """Events that have not finished, soonest first."""
    return _listed_events(under, finished=False)


def past_events(under=None):
    """Events that have finished, most recent first."""
    return _listed_events(under, finished=True)


class EventFilterSet(FacetFilterSet):
    type = TaxonomyFilter(EventType.objects.all(), field_name="event_type", label="Type")
    audience = AudienceFilter()
    topic = TaxonomyFilter(EventTopic.objects.all(), field_name="topics", label="Topic")


def upcoming_events_for(*, types=(), audiences=(), topics=(), count):
    """
    The next few upcoming events matching the chosen facets, and the events index narrowed the same way.

    Each facet is a list of taxonomy objects, and leaving one empty means "any". Returns `([], None)` when the site
    has no events index.
    """
    index = EventsIndexPage.objects.live().first()
    if index is None:
        return [], None

    params = {
        "type": [facet.slug for facet in types],
        "audience": [facet.slug for facet in audiences],
        "topic": [facet.slug for facet in topics],
    }
    events = EventFilterSet(MultiValueDict(params), queryset=upcoming_events(under=index)).qs[:count]
    query = urlencode([(param, slug) for param, slugs in params.items() for slug in slugs])
    return list(events), f"{index.url}?{query}" if query else index.url
