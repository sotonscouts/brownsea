from django.views.defaults import server_error


def test_unknown_urls_render_the_branded_404_page(client, site_tree):
    response = client.get("/this-page-does-not-exist/")

    assert response.status_code == 404
    assert "Page not found" in response.content.decode()
    assert "template-404" in response.content.decode()


def test_the_500_page_is_self_contained(rf):
    response = server_error(rf.get("/"))

    assert response.status_code == 500
    html = response.content.decode()
    assert "Internal server error" in html
    # It must not depend on the site layout, which may be what broke.
    assert "navbar" not in html
