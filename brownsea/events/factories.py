import datetime

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory
from wagtail_factories import PageFactory, StreamFieldFactory

from brownsea.events.models.pages import EventPage, EventsIndexPage
from brownsea.events.models.snippets import EventTopic, EventType
from brownsea.factories import HeadingBlockFactory, RichTextBlockFactory
from brownsea.landing.factories import ChildPagesBlockFactory


class EventTypeFactory(DjangoModelFactory):
    class Meta:
        model = EventType
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Event type {n}")
    slug = factory.Sequence(lambda n: f"event-type-{n}")


class EventTopicFactory(DjangoModelFactory):
    class Meta:
        model = EventTopic
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Event topic {n}")
    slug = factory.Sequence(lambda n: f"event-topic-{n}")


class EventsIndexPageFactory(PageFactory):
    class Meta:
        model = EventsIndexPage

    title = "Events"
    slug = "events"
    introduction = "What's on"


class EventPageFactory(PageFactory):
    """Pass `parent=` an events index. `audiences` and `topics` take lists, e.g. `EventPageFactory(topics=[topic])`."""

    class Meta:
        model = EventPage

    title = factory.Sequence(lambda n: f"Event {n}")
    introduction = "About this event"
    start_date = factory.LazyFunction(lambda: timezone.localdate() + datetime.timedelta(days=7))
    event_type = factory.SubFactory(EventTypeFactory)
    # The admin defaults new pages to this, and listings only show pages that have it.
    show_in_menus = True
    # e.g. `EventPageFactory(body__0__heading__heading="First", body__1__text="<p>Some text</p>")`
    body = StreamFieldFactory(
        {
            "heading": factory.SubFactory(HeadingBlockFactory),
            "text": RichTextBlockFactory,
            "child_pages": factory.SubFactory(ChildPagesBlockFactory),
        }
    )

    @factory.post_generation
    def audiences(self, create, extracted, **kwargs):
        if create and extracted:
            self.audiences.set(extracted)

    @factory.post_generation
    def topics(self, create, extracted, **kwargs):
        if create and extracted:
            self.topics.set(extracted)
