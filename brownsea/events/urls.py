from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
    path("calendar/<slug:slug>/events.json", views.calendar_events_json, name="calendar_events_json"),
]
