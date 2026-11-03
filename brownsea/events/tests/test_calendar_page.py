import pytest

from brownsea.events.models import CalendarPage, ExternalEventCalendar


@pytest.mark.django_db
def test_only_one_calendar_page_can_exist(site_tree):
    home = site_tree["home"]
    calendar = ExternalEventCalendar.objects.create(name="Events", slug="events", ics_url="https://example.org/a.ics")
    assert CalendarPage.can_create_at(home) is True

    home.add_child(
        instance=CalendarPage(title="Calendar", slug="calendar", introduction="Events", external_calendar=calendar)
    )

    assert CalendarPage.can_create_at(home) is False
