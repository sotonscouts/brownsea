from playwright.sync_api import expect
from pytest_bdd import given, parsers, scenarios, then, when

from brownsea.landing.factories import LandingPageFactory

scenarios("pages/landing_page.feature")

# Widths are compared as a share of the page container, with some slack for Bootstrap's gutters.
FULL_WIDTH = 0.9
TWO_THIRDS = (0.55, 0.7)


def _rows(datatable):
    header, *rows = datatable
    return [dict(zip(header, row, strict=True)) for row in rows]


def _container(page):
    return page.locator("main .container").bounding_box()


def _sidebar(page):
    return page.locator("main .col-md-4")


# --- Data ---------------------------------------------------------------------------------------------------------


@given(parsers.parse('the site has a landing page "{title}"'))
@given(parsers.parse('the site has a landing page "{title}" with the introduction "{introduction}"'))
def _landing_page(scenario_state, title, introduction="Introduction"):
    scenario_state["pages"][title] = LandingPageFactory(
        parent=scenario_state["home"], title=title, introduction=introduction
    )


@given(parsers.parse('the landing page "{title}" has the body:'))
def _body(scenario_state, title, datatable):
    """
    Rows with the same section ("links 1", "heading 2", ...) share one block; blocks keep the order written. The
    `title` column is a heading's or text's words, a link's title, or the child pages block's heading.
    """
    sections = {}
    for row in _rows(datatable):
        sections.setdefault(row["section"], []).append(row)

    fields = {}
    for index, (name, rows) in enumerate(sections.items()):
        kind = name.split()[0]
        prefix = f"body__{index}"
        if kind == "heading":
            fields[f"{prefix}__heading__heading"] = rows[0]["title"]
        elif kind == "text":
            fields[f"{prefix}__text"] = f"<p>{rows[0]['title']}</p>"
        elif kind == "children":
            fields[f"{prefix}__child_pages__title"] = rows[0]["title"]
        else:
            for item_index, row in enumerate(rows):
                link = f"{prefix}__link_sections__{item_index}"
                if row["page"]:
                    fields[f"{link}__page__page"] = scenario_state["pages"][row["page"]]
                else:
                    fields[f"{link}__external_link__title"] = row["title"]
                    fields[f"{link}__external_link__url"] = row["url"]

    landing = scenario_state["pages"][title]
    landing.body = LandingPageFactory.build(**fields).body
    landing.save()


@given(parsers.parse('the landing page "{title}" has the sidebar:'))
def _sidebar_blocks(scenario_state, title, datatable):
    fields = {}
    quick_links_at = None
    links = 0
    for row in _rows(datatable):
        if row["block"] == "recent news":
            fields[f"sidebar__{len({k.split('__')[1] for k in fields})}__recent_news"] = True
            continue
        if quick_links_at is None:
            quick_links_at = len({k.split("__")[1] for k in fields})
        link = f"sidebar__{quick_links_at}__quick_links__links__{links}"
        if row["page"]:
            fields[f"{link}__page__page"] = scenario_state["pages"][row["page"]]
        else:
            fields[f"{link}__external_link__title"] = row["title"]
            fields[f"{link}__external_link__url"] = row["url"]
        links += 1

    landing = scenario_state["pages"][title]
    landing.sidebar = LandingPageFactory.build(**fields).sidebar
    landing.save()


# --- Actions ------------------------------------------------------------------------------------------------------


@when(parsers.parse('I click the sidebar link "{name}"'))
def _click_sidebar_link(page, name):
    _sidebar(page).get_by_role("link", name=name, exact=True).click()


# --- Assertions ---------------------------------------------------------------------------------------------------


@then("the landing page sections read:")
def _sections(page, datatable):
    sections = page.locator("main .container > .mb-4")
    expected = [row[0] for row in datatable]
    expect(sections).to_have_count(len(expected))
    for index, text in enumerate(expected):
        expect(sections.nth(index)).to_contain_text(text)


@then("there is no sidebar")
def _no_sidebar(page):
    expect(_sidebar(page)).to_have_count(0)


@then("the introduction spans the full width of the page")
def _full_width(page):
    introduction = page.locator("main .lead").bounding_box()
    assert introduction["width"] / _container(page)["width"] >= FULL_WIDTH


@then("the sidebar sits beside the body, which takes about two thirds of the page")
def _beside(page):
    container = _container(page)
    body = page.locator("main .col-md-8").bounding_box()
    sidebar = _sidebar(page).bounding_box()
    assert body["y"] == sidebar["y"]
    assert body["x"] + body["width"] <= sidebar["x"]
    assert TWO_THIRDS[0] <= body["width"] / container["width"] <= TWO_THIRDS[1], (body, container)


@then("the sidebar sits below the body, and both take the full width")
def _below(page):
    container = _container(page)
    body = page.locator("main .col-md-8").bounding_box()
    sidebar = _sidebar(page).bounding_box()
    assert body["y"] + body["height"] <= sidebar["y"]
    assert body["width"] / container["width"] >= FULL_WIDTH
    assert sidebar["width"] / container["width"] >= FULL_WIDTH


@then("the sidebar quick links are:")
def _quick_links(page, datatable):
    expect(_sidebar(page).locator(".list-group a")).to_have_text([row[0] for row in datatable])


@then(parsers.parse('the sidebar link "{name}" goes to "{url}"'))
def _sidebar_link_target(page, name, url):
    expect(_sidebar(page).get_by_role("link", name=name, exact=True)).to_have_attribute("href", url)
