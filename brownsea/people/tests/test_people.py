import pytest
from django.urls import reverse

from brownsea.news.factories import ArticlePageFactory, NewsIndexPageFactory
from brownsea.people.factories import PersonFactory, PersonRoleFactory, PersonTeamFactory
from brownsea.people.models import PersonRole, PersonTeam


@pytest.fixture
def news_index(site_tree):
    return NewsIndexPageFactory(parent=site_tree["home"])


def test_a_person_can_have_several_roles_in_order(db):
    person = PersonFactory(name="Sam Smith", role="District Commissioner")
    PersonRoleFactory(person=person, title="Trustee", is_current=False)

    assert [str(role) for role in person.roles.all()] == [
        "Sam Smith, District Commissioner",
        "Sam Smith, Trustee (past role)",
    ]
    assert [role.title for role in person.current_roles] == ["District Commissioner"]


def test_teams_are_sorted_by_their_order(db):
    PersonTeamFactory(name="Trustees", sort_order=2)
    PersonTeamFactory(name="District team", sort_order=1)

    assert [team.name for team in PersonTeam.objects.all()] == ["District team", "Trustees"]


def test_an_article_knows_its_author_through_the_role(db, news_index):
    sam = PersonFactory(name="Sam Smith", role="District Commissioner")
    page = ArticlePageFactory(parent=news_index, author_role=sam.roles.get())

    assert page.author == sam


def test_an_article_without_a_role_has_no_author(db, news_index):
    assert ArticlePageFactory(parent=news_index).author is None


def test_removing_a_role_does_not_delete_the_article(db, news_index):
    sam = PersonFactory(role="District Commissioner")
    page = ArticlePageFactory(parent=news_index, author_role=sam.roles.get())

    sam.roles.get().delete()

    page.refresh_from_db()
    assert page.author is None
    assert page.author_role is None


def _edit_data(person, role, **overrides):
    data = {
        "name": person.name,
        "show_in_listing": "",
        "roles-TOTAL_FORMS": "1",
        "roles-INITIAL_FORMS": "1",
        "roles-MIN_NUM_FORMS": "0",
        "roles-MAX_NUM_FORMS": "1000",
        "roles-0-id": str(role.pk),
        "roles-0-ORDER": "1",
        "roles-0-title": role.title,
        "roles-0-is_current": "on",
        "roles-0-DELETE": "",
    }
    return data | overrides


def test_a_role_that_an_article_records_cannot_be_removed(admin_client, news_index, settings):
    # Re-rendering the invalid form needs static files, which the test settings have no manifest for.
    settings.STORAGES = {**settings.STORAGES, "staticfiles": {"BACKEND": "django.core.files.storage.FileSystemStorage"}}
    sam = PersonFactory(role="District Commissioner")
    role = sam.roles.get()
    ArticlePageFactory(parent=news_index, author_role=role)

    response = admin_client.post(
        reverse("wagtailsnippets_people_person:edit", args=[sam.pk]), _edit_data(sam, role, **{"roles-0-DELETE": "1"})
    )

    assert response.status_code == 200
    assert "is the recorded role on an article" in response.content.decode()
    assert PersonRole.objects.filter(pk=role.pk).exists()


def test_a_role_no_article_uses_can_be_removed(admin_client):
    sam = PersonFactory(role="District Commissioner")
    role = sam.roles.get()

    response = admin_client.post(
        reverse("wagtailsnippets_people_person:edit", args=[sam.pk]), _edit_data(sam, role, **{"roles-0-DELETE": "1"})
    )

    assert response.status_code == 302
    assert not PersonRole.objects.filter(pk=role.pk).exists()


def test_roles_can_be_found_in_the_author_chooser_by_person_or_title(admin_client):
    sam = PersonFactory(name="Explorer Smith", role="District Commissioner")
    PersonRoleFactory(person=sam, title="Trustee", is_current=False)
    PersonFactory(name="Kayaker Jones", role="Treasurer")
    url = reverse("person_role_chooser:choose_results")

    by_name = admin_client.get(url, {"q": "Explor"})
    by_title = admin_client.get(url, {"q": "Treasur"})

    assert {str(role) for role in by_name.context["results"]} == {
        "Explorer Smith, District Commissioner",
        "Explorer Smith, Trustee (past role)",
    }
    assert [str(role) for role in by_title.context["results"]] == ["Kayaker Jones, Treasurer"]


def test_the_author_chooser_does_not_offer_to_create_roles(admin_client):
    response = admin_client.get(reverse("person_role_chooser:choose"))

    assert response.status_code == 200
    assert "Create" not in response.content.decode()


def test_people_can_be_found_in_the_person_picker(admin_client):
    wanted = PersonFactory(name="Explorer Smith")
    PersonFactory(name="Kayaker Jones")

    response = admin_client.get(reverse("wagtailsnippetchoosers_people_person:choose_results"), {"q": "Explor"})

    assert list(response.context["results"]) == [wanted]
