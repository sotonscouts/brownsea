from datetime import datetime

import httpx
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from icalendar import Calendar

from .models import ExternalEventCalendar


@login_required
@require_http_methods(["GET"])
@cache_page(60 * 15)  # Cache for 15 minutes
def calendar_events_json(request: HttpRequest, slug: str) -> JsonResponse:
    """
    Fetch ICS calendar feed and convert to JSON for FullCalendar.

    This view fetches the ICS file, parses it server-side, and returns
    events as JSON that FullCalendar can consume directly.
    """
    calendar_obj = get_object_or_404(ExternalEventCalendar, slug=slug)

    try:
        # Fetch the ICS file from the external URL
        response = httpx.get(calendar_obj.ics_url, timeout=10.0, follow_redirects=True)
        response.raise_for_status()

        # Parse the ICS content
        cal = Calendar.from_ical(response.content)

        # Convert events to FullCalendar format
        events = []
        for component in cal.walk():
            if component.name == "VEVENT":
                event = {
                    "title": str(component.get("summary", "")),
                    "start": component.get("dtstart").dt.isoformat() if component.get("dtstart") else None,
                    "end": component.get("dtend").dt.isoformat() if component.get("dtend") else None,
                }

                # Handle all-day events
                if component.get("dtstart") and isinstance(component.get("dtstart").dt, datetime):
                    event["allDay"] = False
                else:
                    event["allDay"] = True

                events.append(event)

        return JsonResponse(events, safe=False)

    except httpx.HTTPError as e:
        return JsonResponse({"error": f"Error fetching calendar: {e!s}"}, status=502)
    except Exception as e:  # noqa: BLE001
        return JsonResponse({"error": f"Error parsing calendar: {e!s}"}, status=500)
