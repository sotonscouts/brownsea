import pytest

from brownsea.factories import publish
from brownsea.landing.factories import LandingPageFactory
from brownsea.news.models.pages import NewsIndexPage


@pytest.mark.django_db
def test_only_one_news_index_page_can_exist(site_tree):
    home = site_tree["home"]
    assert NewsIndexPage.can_create_at(home) is True

    home.add_child(instance=NewsIndexPage(title="News", slug="news", introduction="Latest news"))

    assert NewsIndexPage.can_create_at(home) is False


@pytest.mark.django_db
def test_news_index_pages_only_go_under_the_home_page(site_tree):
    home = site_tree["home"]
    landing = publish(LandingPageFactory(parent=home, title="Landing", slug="landing"))

    assert NewsIndexPage.can_exist_under(home) is True
    assert NewsIndexPage.can_exist_under(landing) is False
