import datetime
import itertools
from decimal import Decimal

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import models
from django.utils import timezone
from modelcluster.fields import ParentalManyToManyField
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel
from wagtail.search import index

from brownsea.core.blocks import EventPageBlock, EventPageSidebarBlock, linked_page_ids
from brownsea.core.models import BasePage
from brownsea.core.utils import StreamField


class CostStreamBlock(blocks.StreamBlock):
    """At most one block, so more complex pricing can be added later as new block types without a schema change."""

    fixed_cost = blocks.DecimalBlock(
        min_value=0,
        decimal_places=2,
        max_digits=8,
        label="Fixed cost",
        help_text="The cost in pounds. Enter 0 for a free event.",
    )

    class Meta:
        max_num = 1


class EventsIndexPage(BasePage):
    template = "pages/events/events_index_page.html"
    parent_page_types = ["home.HomePage"]
    subpage_types = ["events.EventPage"]

    max_count = 1

    introduction = models.TextField()

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        HelpPanel("All published events will be listed."),
    ]
    search_fields = BasePage.search_fields + [index.SearchField("introduction")]

    def get_context(self, request, *args, **kwargs):
        from brownsea.events.filters import EventFilterSet, past_events, upcoming_events

        context = super().get_context(request, *args, **kwargs)

        show_past = request.GET.get("tab") == "past"
        filterset = EventFilterSet(
            request.GET, queryset=past_events(under=self) if show_past else upcoming_events(under=self)
        )
        events = filterset.qs.prefetch_related("audiences")

        paginator = Paginator(events, per_page=settings.APP_SEARCH_RESULTS_PER_PAGE)
        sub_pages = paginator.get_page(request.GET.get("page"))

        context["sub_pages"] = sub_pages
        context["months"] = _group_by_month(sub_pages.object_list)
        context["show_past"] = show_past
        context.update(filterset.listing_context())
        context["hidden_fields"] = [("tab", "past")] if show_past else []
        context["clear_url"] = f"{self.url}?tab=past" if show_past else self.url
        return context


def _group_by_month(events):
    """Events in the order given, grouped under the month they start in."""
    return [
        {"month": month, "events": list(group)}
        for month, group in itertools.groupby(events, key=lambda event: event.start_date.replace(day=1))
    ]


class EventPage(BasePage):
    template = "pages/events/event_page.html"
    parent_page_types = ["events.EventsIndexPage"]
    subpage_types = ["standard_pages.InfoPage", "standard_pages.ProcessPage"]

    introduction = models.TextField(
        help_text="Shown as the lead on the event page, and in event listings and cards.",
    )

    start_date = models.DateField()
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Only for events that run over more than one day.",
    )
    start_time = models.TimeField(null=True, blank=True, help_text="Leave empty for an all-day event.")
    end_time = models.TimeField(null=True, blank=True, help_text="Needs a start time.")

    location = models.CharField(
        max_length=255,
        blank=True,
        help_text="The venue name, such as 'Foxlease Park'. Shown in the details and in listings.",
    )
    address = models.TextField(
        blank=True,
        help_text="The street address and postcode. Shown on the event page only.",
    )
    is_online = models.BooleanField("Online", default=False, help_text="Shown as 'Online' in the event details.")
    online_details = models.CharField(
        max_length=255,
        blank=True,
        help_text="How to join, for example 'Joining details are sent in advance'.",
    )

    event_type = models.ForeignKey("events.EventType", on_delete=models.PROTECT, related_name="events")
    audiences = ParentalManyToManyField(
        "core.Audience",
        blank=True,
        related_name="+",
        help_text="Who this is for. Pages can show only the events for particular audiences.",
    )
    topics = ParentalManyToManyField(
        "events.EventTopic",
        blank=True,
        related_name="events",
        help_text="What this is about. Pages can show only the events on particular topics.",
    )

    cost = StreamField(
        CostStreamBlock(),
        blank=True,
        help_text="Leave empty when the cost is not known and the event page will not show one.",
    )

    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Used when the event is featured on another page.",
    )
    body = StreamField(
        EventPageBlock(),
        blank=True,
        help_text="Optional. Adding content or sidebar blocks moves the details into the sidebar.",
    )
    sidebar = StreamField(
        EventPageSidebarBlock(),
        blank=True,
        help_text="Optional. Short blocks shown below the event details.",
    )

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        MultiFieldPanel(
            [
                FieldPanel("start_date"),
                FieldPanel("end_date"),
                FieldPanel("start_time"),
                FieldPanel("end_time"),
            ],
            "When",
        ),
        MultiFieldPanel(
            [
                FieldPanel("location"),
                FieldPanel("address"),
                FieldPanel("is_online"),
                FieldPanel("online_details"),
            ],
            "Where",
        ),
        MultiFieldPanel(
            [
                FieldPanel("event_type"),
                FieldPanel("audiences", widget=forms.CheckboxSelectMultiple),
                FieldPanel("topics", widget=forms.CheckboxSelectMultiple),
                FieldPanel("cost"),
            ],
            "Classification and cost",
        ),
        FieldPanel("image"),
        FieldPanel("body"),
        FieldPanel("sidebar"),
    ]
    search_fields = BasePage.search_fields + [
        index.SearchField("introduction"),
        index.SearchField("body"),
    ]

    class Meta:
        verbose_name = "Event page"

    def clean(self):
        super().clean()
        errors = {}
        if self.start_date and self.end_date and self.end_date < self.start_date:
            errors["end_date"] = "The end date cannot be before the start date."
        if self.end_time and not self.start_time:
            errors["end_time"] = "Add a start time to give a time range."
        elif self.start_time and self.end_time and self.is_single_day and self.end_time <= self.start_time:
            errors["end_time"] = "The end time must be after the start time."
        if errors:
            raise ValidationError(errors)

    @property
    def last_day(self) -> datetime.date | None:
        return self.end_date or self.start_date

    @property
    def is_single_day(self) -> bool:
        return self.end_date is None or self.end_date == self.start_date

    @property
    def starts_on(self) -> datetime.datetime | None:
        """When the event starts, in the local time zone. Events with no start time begin at midnight."""
        if self.start_date is None:
            return None
        return timezone.make_aware(datetime.datetime.combine(self.start_date, self.start_time or datetime.time.min))

    @property
    def is_upcoming(self) -> bool:
        """An event is upcoming until the end of its last day."""
        return self.last_day is not None and self.last_day >= timezone.localdate()

    @property
    def has_ended(self) -> bool:
        return not self.is_upcoming

    @property
    def has_extra_content(self) -> bool:
        """Events with body content or sidebar blocks use the sidebar layout. Otherwise the details fill the width."""
        return bool(self.body) or bool(self.sidebar)

    @property
    def cost_display(self) -> str | None:
        """'Free', or an amount such as '£12.50'. None when no cost is set."""
        for block in self.cost:
            amount = Decimal(block.value)
            return "Free" if amount == 0 else f"£{amount:.2f}"
        return None

    @property
    def when_lines(self) -> list[str]:
        """The date, then the time, as lines to show one under the other."""
        if not self.start_date:
            return []
        start, end = self.start_date, self.last_day
        if self.is_single_day:
            lines = [_format_date(start, weekday=True, year=True)]
            if self.start_time and self.end_time:
                lines.append(f"{_format_time(self.start_time)} to {_format_time(self.end_time)}")
            elif self.start_time:
                lines.append(f"From {_format_time(self.start_time)}")
            return lines

        same_year = start.year == end.year
        same_month = same_year and start.month == end.month
        first = _format_date(start, year=not same_year, month=not same_month)
        lines = [f"{first} to {_format_date(end, year=True)}"]
        if self.start_time and self.end_time:
            lines.append(f"Starts {_format_time(self.start_time)}, ends {_format_time(self.end_time)}")
        elif self.start_time:
            lines.append(f"Starts {_format_time(self.start_time)}")
        return lines

    @property
    def when_summary(self) -> str:
        """The date and time on one line, for listings."""
        first, *rest = self.when_lines
        if rest:
            time = rest[0]
            return f"{first}, {time[0].lower()}{time[1:]}"
        return first

    def get_linked_page_ids(self):
        """The pages linked from this page's body and sidebar, so automatic lists can leave them out."""
        return [*linked_page_ids(self.body), *linked_page_ids(self.sidebar)]


def _format_date(date, *, weekday=False, year=False, month=True):
    parts = [f"{date.day}"]
    if month:
        parts.append(date.strftime("%B"))
    if year:
        parts.append(str(date.year))
    text = " ".join(parts)
    return f"{date.strftime('%A')} {text}" if weekday else text


def _format_time(time):
    return time.strftime("%H:%M")
