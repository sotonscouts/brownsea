import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_search_redirects_anonymous_users_to_login(client):
    response = client.get(reverse("search"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


@pytest.mark.django_db
def test_authenticated_users_can_access_search(authenticated_client):
    response = authenticated_client.get(reverse("search"))

    assert response.status_code == 200
