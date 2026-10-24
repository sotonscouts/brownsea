from django.urls import path

from . import views

app_name = "gis"

urlpatterns = [
    path("token/", views.woodmap_token, name="token"),
]
