from django.urls import reverse
from wagtail.admin.menu import admin_menu


def test_page_types_guide_url():
    assert reverse("page_types_guide") == "/admin/page-types/"


def test_page_types_guide_requires_login(client):
    response = client.get(reverse("page_types_guide"))

    assert response.status_code == 302
    assert "login" in response["Location"]


def test_help_menu_links_to_page_types_guide(rf, admin_user):
    request = rf.get("/admin/")
    request.user = admin_user

    help_menu = next(item for item in admin_menu.menu_items_for_request(request) if item.name == "help")
    items = help_menu.menu.menu_items_for_request(request)

    assert any(item.url == reverse("page_types_guide") for item in items)
