from django.urls import path

from brownsea.core.views import magic_links as magic_links_views

app_name = "core"

urlpatterns = [
    path(
        "magic-links/<int:page_id>/",
        magic_links_views.magic_links_panel,
        name="magic_links_panel",
    ),
    path(
        "magic-links/<int:page_id>/create/",
        magic_links_views.magic_links_create,
        name="magic_links_create",
    ),
    path(
        "magic-links/<int:page_id>/<uuid:token_id>/revoke/",
        magic_links_views.magic_links_revoke,
        name="magic_links_revoke",
    ),
]
