import hmac
from datetime import date, datetime

import httpx
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from icalendar import Calendar

from .models import ExternalEventCalendar


@require_http_methods(["GET", "OPTIONS"])
@cache_page(60 * 15)  # Cache for 15 minutes
def calendar_events_json(request: HttpRequest, slug: str) -> JsonResponse | HttpResponse:
    """
    Fetch ICS calendar feed and convert to JSON for FullCalendar.

    This view fetches the ICS file, parses it server-side, and returns
    events as JSON that FullCalendar can consume directly.
    """
    calendar_obj = get_object_or_404(ExternalEventCalendar, slug=slug)

    if calendar_obj.external_cors_origin:
        cors_origin = calendar_obj.external_cors_origin
    else:
        cors_origin = f"{request.scheme}://{request.get_host()}"

    # 3. Handle the Preflight (OPTIONS) request
    if request.method == "OPTIONS":
        response = HttpResponse()
        response["Access-Control-Allow-Origin"] = cors_origin
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        return response

    if (auth_header := request.headers.get("Authorization")) and calendar_obj.external_bearer_token:
        external_request = True

        if hmac.compare_digest(auth_header, calendar_obj.external_bearer_token):
            pass  # Authorised
        else:
            return JsonResponse({"error": "Unauthorized"}, status=401)
    else:
        external_request = False
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)

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
                dtstart = component.get("dtstart")
                dtend = component.get("dtend")

                start = None
                end = None
                all_day = False
                if dtstart:
                    start = dtstart.dt

                if start and dtend:
                    end = dtend.dt
                    if isinstance(dtend.dt, datetime):
                        if end.day != start.day:
                            end = start.replace(hour=23, minute=59, second=59)
                            all_day = True

                if isinstance(start, date) and isinstance(end, date):
                    all_day = True

                event = {
                    "title": "Booked" if external_request else str(component.get("summary", "")),
                    "start": start.isoformat() if start else None,
                    "end": end.isoformat() if end else None,
                    "allDay": all_day,
                }

                events.append(event)

        return JsonResponse(
            events,
            safe=False,
            headers={
                "Cache-Control": "public, max-age=900",
                "Access-Control-Allow-Origin": cors_origin,
                "Access-Control-Allow-Headers": "Authorization, Content-Type",
            },
        )

    except httpx.HTTPError as e:
        return JsonResponse({"error": f"Error fetching calendar: {e!s}"}, status=502)
    except Exception as e:  # noqa: BLE001
        return JsonResponse({"error": f"Error parsing calendar: {e!s}"}, status=500)
