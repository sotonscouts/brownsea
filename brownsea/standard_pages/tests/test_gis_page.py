import pytest

from brownsea.standard_pages.models import GISPage


@pytest.mark.django_db
def test_only_one_gis_page_can_exist(site_tree):
    home = site_tree["home"]
    assert GISPage.can_create_at(home) is True

    home.add_child(instance=GISPage(title="Map", slug="map", introduction="A map"))

    assert GISPage.can_create_at(home) is False
