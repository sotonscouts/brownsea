from wagtail.admin.menu import admin_menu

from brownsea.core.models import Audience, Taxonomy
from brownsea.news.models import NewsTopic, NewsType


def test_taxonomy_models_share_the_base():
    assert all(issubclass(model, Taxonomy) for model in (Audience, NewsType, NewsTopic))


def test_taxonomy_models_are_named_and_sorted_by_name(db):
    Audience.objects.create(name="Volunteers", slug="volunteers")
    Audience.objects.create(name="Beavers", slug="beavers")

    assert [str(audience) for audience in Audience.objects.all()] == ["Beavers", "Volunteers"]


def test_taxonomies_menu_lists_every_taxonomy(rf, admin_user):
    request = rf.get("/admin/")
    request.user = admin_user

    menu = next(item for item in admin_menu.menu_items_for_request(request) if item.name == "taxonomies")
    labels = [item.label for item in menu.menu.menu_items_for_request(request)]

    assert labels == ["Audiences", "News Types", "News Topics"]
