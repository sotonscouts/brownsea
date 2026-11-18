import json

from playwright.sync_api import expect
from pytest_bdd import given, parsers, scenarios, then, when

from brownsea.events.factories import EventPageFactory

scenarios("pages/event_page.feature")

# Widths are compared as a share of the page container, with some slack for Bootstrap's gutters.
FULL_WIDTH = 0.9
TWO_THIRDS = (0.55, 0.7)

BODY_BLOCKS = {
    "heading": lambda index, value: {f"body__{index}__heading__heading": value},
    "text": lambda index, value: {f"body__{index}__text": f"<p>{value}</p>"},
}


def _rows(datatable):
    header, *rows = datatable
    return [dict(zip(header, row, strict=True)) for row in rows]


def _words(text):
    return " ".join(text.split())


def _box(locator):
    return locator.bounding_box()


def _container(page):
    return page.locator("main .container").bounding_box()


def _facts(page):
    return page.locator("main .event-facts")


def _fact_rows(page):
    return _facts(page).locator("dl > div")


def _key_dates(page):
    return page.locator("main .card").filter(has=page.get_by_role("heading", name="Key dates"))


# --- Data ---------------------------------------------------------------------------------------------------------


@given(parsers.parse('the event "{title}" has the body:'))
def _body(scenario_state, title, datatable):
    fields = {}
    for index, row in enumerate(_rows(datatable)):
        fields.update(BODY_BLOCKS[row["block"]](index, row["value"]))
    event = scenario_state["pages"][title]
    event.body = EventPageFactory.build(**fields).body
    event.save()


@given(parsers.parse('the event "{title}" has the child pages block'))
def _child_pages(scenario_state, title):
    event = scenario_state["pages"][title]
    event.body = EventPageFactory.build(body__0__child_pages__title="").body
    event.save()


@given(parsers.parse('the event "{title}" has the key dates:'))
def _key_dates_data(scenario_state, title, datatable):
    """Columns: when and what are required. links to is the title of a page the description links to."""
    dates = []
    for index, row in enumerate(_rows(datatable)):
        target = scenario_state["pages"][row["links to"]] if row.get("links to") else None
        dates.append(
            {
                "type": "item",
                "id": f"date-{index}",
                "value": {"when": row["when"], "what": row["what"], "page": target.id if target else None},
            }
        )
    event = scenario_state["pages"][title]
    event.sidebar = json.dumps(
        [{"type": "key_dates", "id": "key-dates", "value": {"heading": "Key dates", "dates": dates}}]
    )
    event.save()


# --- Actions ------------------------------------------------------------------------------------------------------


@when(parsers.parse('I click the key date "{name}"'))
def _click_key_date(page, name):
    _key_dates(page).get_by_role("link", name=name).click()


@when(parsers.parse('I click the event detail "{name}"'))
def _click_detail(page, name):
    _facts(page).get_by_role("link", name=name, exact=True).click()


# --- Assertions ---------------------------------------------------------------------------------------------------


@then("the event details are:")
def _details(page, datatable):
    expect(_fact_rows(page)).to_have_count(len(datatable))
    actual = [
        (_words(row.locator("dt").text_content()), _words(row.locator("dd").inner_text()))
        for row in _fact_rows(page).all()
    ]
    assert actual == [tuple(row) for row in datatable]


@then("the event details span the full width of the page")
def _details_full_width(page):
    assert _box(_facts(page))["width"] >= _container(page)["width"] * FULL_WIDTH


@then("the event details are laid out in columns")
def _details_in_columns(page):
    first, second, third = (_box(row) for row in _fact_rows(page).all()[:3])
    assert abs(first["y"] - second["y"]) < 2
    assert abs(first["y"] - third["y"]) < 2
    assert first["x"] < second["x"] < third["x"]


@then("the event details are in one column")
def _details_in_one_column(page):
    boxes = [_box(row) for row in _fact_rows(page).all()]
    assert len(boxes) > 1
    assert all(abs(box["x"] - boxes[0]["x"]) < 2 for box in boxes)
    assert boxes[0]["y"] < boxes[1]["y"]


@then("there is no sidebar")
def _no_sidebar(page):
    expect(page.locator("main .event-layout")).to_have_count(0)


@then("the event details sit beside the body, which takes about two thirds of the page")
def _details_beside_body(page):
    body = _box(page.locator(".event-layout__body"))
    facts = _box(page.locator(".event-layout__facts"))
    assert facts["x"] >= body["x"] + body["width"]
    assert abs(facts["y"] - body["y"]) < 20
    low, high = TWO_THIRDS
    assert low <= body["width"] / _container(page)["width"] <= high


@then("the key dates are below the event details")
def _key_dates_below_details(page):
    facts = _box(page.locator(".event-layout__facts"))
    key_dates = _box(_key_dates(page))
    assert key_dates["y"] >= facts["y"] + facts["height"]
    assert abs(key_dates["x"] - facts["x"]) < 2


@then("the event details are above the body")
def _details_above_body(page):
    facts = _box(page.locator(".event-layout__facts"))
    body = _box(page.locator(".event-layout__body"))
    assert facts["y"] + facts["height"] <= body["y"]


@then("the key dates are below the body")
def _key_dates_below_body(page):
    body = _box(page.locator(".event-layout__body"))
    assert _box(_key_dates(page))["y"] >= body["y"] + body["height"]


@then("the event body reads:")
def _event_body(page, datatable):
    expect(page.locator(".event-layout__body > div").locator("h2, p")).to_have_text([row[0] for row in datatable])


@then("the key dates read:")
def _key_dates_read(page, datatable):
    items = _key_dates(page).locator("li").all()
    actual = [tuple(line.strip() for line in item.inner_text().splitlines() if line.strip()) for item in items]
    assert actual == [tuple(row) for row in datatable]


@then(parsers.parse('the key date "{name}" is not a link'))
def _key_date_not_a_link(page, name):
    item = _key_dates(page).locator("li").filter(has_text=name)
    expect(item).to_have_count(1)
    expect(item.locator("a")).to_have_count(0)
