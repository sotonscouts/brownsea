"""Steps shared by every feature."""

import datetime
import re
from datetime import timedelta

import pytest
from django.utils import timezone
from django.utils.text import slugify
from playwright.sync_api import expect
from pytest_bdd import given, parsers, then, when
from wagtail_factories import ImageFactory

from brownsea.core.factories import AudienceFactory, PageMagicLinkFactory
from brownsea.core.magic_links import build_magic_link_url
from brownsea.core.models import PageAccessLevel
from brownsea.factories import (
    AdminUserFactory,
    HomePageFactory,
    IndexPageFactory,
    InfoPageFactory,
    PageViewRestrictionFactory,
    UserFactory,
)
from brownsea.navigation.factories import NavigationSettingsFactory, nav_link
from brownsea.news.factories import ArticlePageFactory, NewsIndexPageFactory, NewsTopicFactory, NewsTypeFactory
from brownsea.people.factories import PersonFactory, PersonRoleFactory


def _link(scope, name):
    """A link by its visible text. Icon glyphs in the link are part of its accessible name, so allow for them."""
    return scope.get_by_role("link", name=re.compile(rf"^\W*{re.escape(name)}$"))


def _page(state, title):
    return state["pages"][title]


def _cards(page):
    return page.locator("main .card").filter(has=page.locator(".card-title"))


def _card(page, title):
    return _cards(page).filter(has=page.get_by_role("heading", name=title, exact=True))


def _rows(datatable):
    header, *rows = datatable
    return [dict(zip(header, row, strict=True)) for row in rows]


@pytest.fixture
def scenario_state():
    """Scratch space for sharing values between the steps of a scenario."""
    return {"pages": {}, "magic_links": {}}


# --- Data ---------------------------------------------------------------------------------------------------------


@given("the intranet has a site")
def _site(make_site, scenario_state):
    site, home = make_site()
    scenario_state.update(site=site, home=home)
    scenario_state["pages"]["Home"] = home


@given("the home page is public")
def _public_home(scenario_state):
    home = scenario_state["home"]
    home.access_level = "public"
    home.save()


@given("I am logged in")
def _logged_in(log_in):
    log_in(UserFactory())


ACCESS_LEVELS = {
    "public": PageAccessLevel.PUBLIC,
    "logged in only": PageAccessLevel.LOGGED_IN,
    "magic link only": PageAccessLevel.MAGIC_LINK,
    "inherited": PageAccessLevel.INHERIT,
}


@given(parsers.re(r'the page "(?P<title>[^"]+)" is (?P<level>public|logged in only|magic link only|inherited)'))
def _access_level(scenario_state, title, level):
    page = _page(scenario_state, title)
    page.access_level = ACCESS_LEVELS[level]
    page.save()


@given(parsers.parse('the page "{title}" is hidden from menus'))
def _hidden_from_menus(scenario_state, title):
    page = _page(scenario_state, title)
    page.show_in_menus = False
    page.save()


@given(parsers.parse('the page "{title}" is unpublished'))
def _unpublished(scenario_state, title):
    _page(scenario_state, title).unpublish()


@given(parsers.parse('the page "{parent}" has the info pages:'))
def _info_pages(scenario_state, parent, datatable):
    _, *rows = datatable  # first row is the header: title | introduction
    for title, introduction in rows:
        scenario_state["pages"][title] = InfoPageFactory(
            parent=_page(scenario_state, parent), title=title, introduction=introduction
        )


@given(parsers.parse('the page "{title}" has the password "{password}"'))
def _password_protected(scenario_state, title, password):
    PageViewRestrictionFactory(page=_page(scenario_state, title), password=password)


@given(parsers.parse('the page "{title}" has a magic link labelled "{label}"'))
def _magic_link(scenario_state, title, label):
    scenario_state["magic_links"][label] = PageMagicLinkFactory(page=_page(scenario_state, title), label=label)


@given(parsers.parse('the page "{title}" has a revoked magic link labelled "{label}"'))
def _revoked_magic_link(scenario_state, title, label):
    scenario_state["magic_links"][label] = PageMagicLinkFactory(
        page=_page(scenario_state, title), label=label, revoked_at=timezone.now()
    )


@given(parsers.parse('the page "{title}" has an expired magic link labelled "{label}"'))
def _expired_magic_link(scenario_state, title, label):
    scenario_state["magic_links"][label] = PageMagicLinkFactory(
        page=_page(scenario_state, title), label=label, expires_at=timezone.now() - timedelta(days=1)
    )


@given(parsers.parse('a user "{username}" exists'))
def _user(username):
    UserFactory(username=username)


@given(parsers.parse('an editor "{username}" exists'))
def _editor(username):
    AdminUserFactory(username=username)


@given("I am logged in as an editor")
def _logged_in_as_editor(log_in):
    log_in(AdminUserFactory())


@given(parsers.parse('the page "{parent}" has an info page "{title}"'))
@given(parsers.parse('the site has an info page "{title}"'))
def _info_page(scenario_state, title, parent="Home"):
    scenario_state["pages"][title] = InfoPageFactory(parent=_page(scenario_state, parent), title=title)


@given(parsers.parse('the page "{parent}" has an info page "{title}" with the introduction "{introduction}"'))
@given(parsers.parse('the site has an info page "{title}" with the introduction "{introduction}"'))
def _info_page_with_introduction(scenario_state, title, introduction, parent="Home"):
    scenario_state["pages"][title] = InfoPageFactory(
        parent=_page(scenario_state, parent), title=title, introduction=introduction
    )


@given(parsers.parse('the page "{parent}" has an index page "{title}"'))
@given(parsers.parse('the site has an index page "{title}"'))
def _index_page(scenario_state, title, parent="Home"):
    scenario_state["pages"][title] = IndexPageFactory(parent=_page(scenario_state, parent), title=title)


@given(parsers.parse('the site has an info page "{title}" with the headings:'))
def _info_page_with_headings(scenario_state, title, datatable):
    headings = {f"body__{index}__heading__heading": row[0] for index, row in enumerate(datatable)}
    scenario_state["pages"][title] = InfoPageFactory(parent=scenario_state["home"], title=title, **headings)


BODY_BLOCKS = {
    "heading": lambda index, value: {f"body__{index}__heading__heading": value},
    "text": lambda index, value: {f"body__{index}__text": f"<p>{value}</p>"},
    "quote": lambda index, value: {f"body__{index}__quote__quote": value},
}


@given(parsers.parse('the site has an info page "{title}" with the body:'))
def _info_page_with_body(scenario_state, title, datatable):
    _, *rows = datatable  # first row is the header: block | value
    body = {}
    for index, (block, value) in enumerate(rows):
        body.update(BODY_BLOCKS[block](index, value))
    scenario_state["pages"][title] = InfoPageFactory(parent=scenario_state["home"], title=title, **body)


@given("the navigation has the links:")
def _navigation_links(scenario_state, datatable):
    _, *rows = datatable  # first row is the header: title | page | url
    items = [
        nav_link(title=title, page=_page(scenario_state, page) if page else None, url=url) for title, page, url in rows
    ]
    NavigationSettingsFactory(site=scenario_state["site"], primary_navigation=items)


@given(parsers.parse('the navigation has a "{title}" menu with the group "{heading}" containing the pages:'))
def _navigation_menu(scenario_state, title, heading, datatable):
    pages = [_page(scenario_state, row[0]) for row in datatable]
    NavigationSettingsFactory(
        site=scenario_state["site"], primary_navigation=[nav_link(title=title, groups={heading: pages})]
    )


@given(
    parsers.parse(
        'the navigation has a "{title}" menu featuring the page "{featured}" with the group "{heading}" '
        "containing the pages:"
    )
)
def _navigation_menu_with_featured_page(scenario_state, title, featured, heading, datatable):
    pages = [_page(scenario_state, row[0]) for row in datatable]
    item = nav_link(
        title=title,
        groups={heading: pages},
        featured_page=_page(scenario_state, featured),
        featured_image=ImageFactory(),
    )
    NavigationSettingsFactory(site=scenario_state["site"], primary_navigation=[item])


@given(parsers.parse('"{name}" has the past role "{past}" and the current role "{current}"'))
def _person_roles(scenario_state, name, past, current):
    person = PersonFactory(name=name, role=past, role__is_current=False)
    PersonRoleFactory(person=person, title=current)
    scenario_state.setdefault("people", {})[name] = person


@given("anonymous visitors can see the menu")
def _menu_for_anonymous(settings):
    settings.APP_SHOW_MENU_WHEN_UNAUTHENTICATED = True


@given("the home page has the sections:")
def _sections(scenario_state, datatable):
    """Rows with the same section ("featured 1", "links 2", ...) share one section; sections keep the order written."""
    sections = {}
    for row in _rows(datatable):
        sections.setdefault(row["section"], []).append(row)

    fields = {}
    for index, (name, items) in enumerate(sections.items()):
        kind = "featured_sections" if name.startswith("featured") else "link_sections"
        for item_index, item in enumerate(items):
            prefix = f"body__{index}__{kind}__{item_index}"
            if item["page"]:
                fields[f"{prefix}__page__page"] = scenario_state["pages"][item["page"]]
            else:
                fields[f"{prefix}__external_link__title"] = item["title"]
                fields[f"{prefix}__external_link__url"] = item["url"]

    home = scenario_state["home"]
    home.body = HomePageFactory.build(**fields).body
    home.save()


@given("the site has a news index")
def _news_index(scenario_state):
    scenario_state["news_index"] = NewsIndexPageFactory(parent=scenario_state["home"])
    scenario_state["pages"]["News"] = scenario_state["news_index"]


def _facets(factory, value):
    return [factory(name=name, slug=slugify(name)) for name in value.split(", ") if name]


@given("the news has the articles:")
def _articles(scenario_state, datatable):
    """Columns: title, published and type are required; introduction, image (yes, or tall for a portrait photo), topics and audiences (comma-separated) are optional."""
    for row in _rows(datatable):
        extra = {}
        if row.get("image") == "yes":
            extra["image"] = ImageFactory()
        elif row.get("image") == "tall":
            extra["image"] = ImageFactory(file__width=400, file__height=1200)
        if row.get("introduction"):
            extra["introduction"] = row["introduction"]
        extra["topics"] = _facets(NewsTopicFactory, row.get("topics", ""))
        extra["audiences"] = _facets(AudienceFactory, row.get("audiences", ""))
        scenario_state["pages"][row["title"]] = ArticlePageFactory(
            parent=scenario_state["news_index"],
            title=row["title"],
            publication_date=datetime.date.fromisoformat(row["published"]),
            news_type=NewsTypeFactory(name=row["type"], slug=slugify(row["type"])),
            **extra,
        )


@given(parsers.parse("news is shown {count:d} articles to a page"))
def _news_page_size(settings, count):
    settings.APP_SEARCH_RESULTS_PER_PAGE = count


@given("I am using a phone")
@when("I am using a phone")
def _phone(page):
    page.set_viewport_size({"width": 375, "height": 800})


# --- Actions ------------------------------------------------------------------------------------------------------


@when(parsers.parse('I visit "{path}"'))
def _visit(page, scenario_state, path):
    scenario_state["response"] = page.goto(path)


@when(parsers.parse('I open the magic link "{label}"'))
def _open_magic_link(page, scenario_state, label):
    page.goto(build_magic_link_url(scenario_state["magic_links"][label]))


@when(parsers.parse('I log in as "{username}" with the password "{password}"'))
def _log_in_with_form(page, username, password):
    page.get_by_label("Username").fill(username)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Login").click()


@when(parsers.parse('I click "{name}" in the navigation'))
def _click_in_navigation(page, name):
    _link(page.locator("nav.navbar"), name).click()


@when("I open the navigation menu")
def _open_navigation_menu(page):
    page.get_by_role("button", name="Toggle navigation").click()


@when(parsers.parse('I click the "{name}" button in the navigation'))
def _click_button_in_navigation(page, name):
    # The logout button is icon-only, so it is found by its title.
    page.locator("nav.navbar").get_by_title(name).click()


@when(parsers.parse('I search for "{query}"'))
def _search(page, query):
    box = page.get_by_role("searchbox", name="Search", exact=True)
    box.fill(query)
    box.press("Enter")


@when(parsers.parse('I open the search result "{title}"'))
def _open_result(page, title):
    page.locator(".list-group-item").filter(has_text=title).click()


@when(parsers.parse('I click "{name}" in the breadcrumbs'))
def _click_in_breadcrumbs(page, name):
    page.get_by_label("breadcrumb").get_by_role("link", name=name, exact=True).click()


@when(parsers.parse('I click "{name}" in the menu'))
def _click_in_menu(page, name):
    page.locator(".dropdown-menu.show").get_by_role("link", name=name, exact=True).click()


@when(parsers.parse('I click the featured card "{title}" in the menu'))
def _click_featured_card_in_menu(page, title):
    card = page.locator(".dropdown-menu.show .card").filter(has=page.get_by_role("heading", name=title, exact=True))
    card.get_by_role("link").click()


@when(parsers.parse('I open the card "{title}"'))
def _open_card(page, title):
    _card(page, title).get_by_role("link").first.click()


@when(parsers.parse('I click "{name}"'))
def _click_link(page, name):
    page.get_by_role("main").get_by_role("link", name=re.compile(rf"^{re.escape(name)}\b")).click()


# --- Assertions ---------------------------------------------------------------------------------------------------


@then(parsers.parse("the response status is {status:d}"))
def _status(scenario_state, status):
    assert scenario_state["response"].status == status


@then(parsers.parse('I see the heading "{text}"'))
def _heading(page, text):
    expect(page.get_by_role("heading", name=text, level=1)).to_be_visible()


@then(parsers.parse('I see the text "{text}"'))
def _text(page, text):
    expect(page.get_by_text(text).first).to_be_visible()


@then(parsers.parse('I do not see the heading "{text}"'))
def _no_heading(page, text):
    expect(page.get_by_role("heading", name=text, level=1)).to_have_count(0)


@then(parsers.parse('I do not see the text "{text}"'))
def _no_text(page, text):
    expect(page.get_by_text(text)).to_have_count(0)


@then(parsers.parse('I am on "{path}"'))
def _on_path(page, base_url, path):
    expect(page).to_have_url(f"{base_url}{path}")


@then("I am asked to log in")
def _asked_to_log_in(page):
    # The page asked for is kept in `next`, including any query string, so only the start of the URL is fixed.
    expect(page).to_have_url(re.compile(r"/accounts/login/\?next="))


@then(parsers.parse('I see "{name}" in the navigation'))
def _see_in_navigation(page, name):
    expect(_link(page.locator("nav.navbar"), name)).to_be_visible()


@then(parsers.parse('I do not see "{name}" in the navigation'))
def _not_in_navigation(page, name):
    expect(_link(page.locator("nav.navbar"), name)).to_have_count(0)


@then(parsers.parse('I see the "{name}" button in the navigation'))
def _button_in_navigation(page, name):
    # The logout button is icon-only, so it is found by its title.
    expect(page.locator("nav.navbar").get_by_title(name)).to_be_visible()


@then("I see the search results:")
def _results(page, datatable):
    expect(page.locator(".list-group-item h3")).to_have_text([row[0] for row in datatable])


@then(parsers.parse('the breadcrumbs are "{trail}"'))
def _breadcrumbs(page, trail):
    links = page.get_by_label("breadcrumb").get_by_role("link")
    expect(links).to_have_text(trail.split(" > "))


@then("there are no breadcrumbs")
def _no_breadcrumbs(page):
    expect(page.get_by_label("breadcrumb")).to_have_count(0)


@then(parsers.parse('the browser tab is titled "{title}"'))
def _tab_title(page, title):
    expect(page).to_have_title(re.compile(re.escape(title)))


@then("the browser reported no errors")
def _no_browser_errors(browser_errors):
    assert browser_errors == []


@then(parsers.parse('the menu shows a featured card "{title}" with the introduction "{introduction}"'))
def _menu_featured_card(page, title, introduction):
    card = page.locator(".dropdown-menu.show .card")
    expect(card.get_by_role("heading", name=title, exact=True)).to_be_visible()
    expect(card.get_by_text(introduction)).to_be_visible()
    expect(card.locator("img")).to_be_visible()


@then("the menu shows no featured card")
def _menu_no_featured_card(page):
    expect(page.locator(".dropdown-menu.show")).to_be_visible()
    expect(page.locator(".dropdown-menu .card")).to_have_count(0)


@then("the menu shows no visible featured card")
def _menu_no_visible_featured_card(page):
    expect(page.locator(".dropdown-menu .card")).to_be_hidden()


@then("I see the cards:")
def _see_cards(page, datatable):
    expect(_cards(page).locator(".card-title")).to_have_text([row[0] for row in datatable])


@then(parsers.parse('the card "{title}" links to "{url}"'))
def _card_link(page, title, url):
    expect(_card(page, title).get_by_role("link").first).to_have_attribute("href", url)


@then("the card images have loaded")
def _images_loaded(page):
    images = page.locator("main img:visible")
    expect(images.first).to_be_visible()
    for image in images.all():
        expect(image).to_have_js_property("complete", True)
        assert image.evaluate("img => img.naturalWidth") > 0, image.get_attribute("src")


@then("the news index lists:")
def _news_index_lists(page, datatable):
    expect(page.locator("main .card-title")).to_have_text([row[0] for row in datatable])


@then("the recent news is:")
def _recent_news_is(page, datatable):
    card = page.locator(".card").filter(has=page.get_by_role("heading", name="Recent News"))
    expect(card.locator(".list-group-item h3")).to_have_text([row[0] for row in datatable])
