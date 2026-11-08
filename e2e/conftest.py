import json
import os
import re
from pathlib import Path

import pytest
from wagtail.models import Page, Site

# Playwright's sync API runs an event loop in the test thread, which makes Django refuse ORM calls.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

REPORT_DIR = Path(__file__).resolve().parent.parent / "reports" / "e2e"
SCREENSHOT_DIR = REPORT_DIR / "screenshots"
SCREENSHOT_INDEX = SCREENSHOT_DIR / "index.json"


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


@pytest.fixture(scope="session", autouse=True)
def _reset_screenshots():
    """Start each run with a clean screenshot directory; the index is written at session end."""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    for stale in SCREENSHOT_DIR.glob("*.png"):
        stale.unlink()
    SCREENSHOT_INDEX.write_text("{}")


@pytest.fixture(scope="session")
def _initial_data(django_db_setup, django_db_blocker):
    """The rows migrations create (root page, locale, ...), which every scenario's flush deletes."""
    from django.db import connection

    with django_db_blocker.unblock():
        return connection.creation.serialize_db_to_string()


@pytest.fixture(autouse=True)
def _e2e_database(django_db_serialized_rollback, _initial_data, transactional_db, live_server):
    """Set up the test database and the live server up front, in that order, with the migration data in place.

    Steps request fixtures dynamically, which is too late for pytest-django to guarantee the test database
    (rather than the configured one) is the one in use.

    Each scenario's flush deletes the rows migrations create, so Django's serialized rollback restores them. Django
    only does that when the connection carries the serialized data, but Playwright's sync API runs an event loop,
    which gives the tests a different connection from the one that was serialized at setup, so attach it here.
    """
    from django.db import connection

    if not hasattr(connection, "_test_serialized_contents"):
        connection._test_serialized_contents = _initial_data


@pytest.fixture(scope="session")
def base_url(live_server):
    return live_server.url


@pytest.fixture
def scenario_state():
    """Scratch space for sharing values between steps in a scenario."""
    return {}


@pytest.fixture(autouse=True)
def browser_errors(page, live_server):
    """Collect problems the browser reports for this app (not for third-party hosts such as CDNs)."""
    errors = []

    def is_local(url):
        return url.startswith(live_server.url)

    page.on("pageerror", lambda error: errors.append(f"Uncaught exception: {error}"))
    page.on(
        "console",
        lambda msg: msg.type == "error" and is_local(msg.location.get("url", "")) and errors.append(msg.text),
    )
    page.on("requestfailed", lambda request: is_local(request.url) and errors.append(f"Request failed: {request.url}"))
    page.on(
        "response",
        lambda response: (
            is_local(response.url)
            and response.status >= 500
            and errors.append(f"{response.status} from {response.url}")
        ),
    )
    return errors


@pytest.fixture
def log_in(context, live_server):
    """Log a user in by giving the browser a session cookie, which is much faster than using the login form."""
    from django.conf import settings
    from django.test import Client

    def _log_in(user):
        client = Client()
        client.force_login(user)
        context.add_cookies(
            [
                {
                    "name": settings.SESSION_COOKIE_NAME,
                    "value": client.cookies[settings.SESSION_COOKIE_NAME].value,
                    "url": live_server.url,
                }
            ]
        )

    return _log_in


@pytest.fixture
def make_site(live_server):
    """Replace the default Site with one that resolves to the live server."""
    from wagtail_factories import SiteFactory

    from brownsea.factories import HomePageFactory, publish

    def _make_site():
        Site.objects.all().delete()
        home = publish(HomePageFactory(parent=Page.get_first_root_node(), title="Home", slug="e2e-home"))
        host, _, port = live_server.url.removeprefix("http://").partition(":")
        site = SiteFactory(
            hostname=host,
            port=int(port or 80),
            root_page=home,
            is_default_site=True,
            site_name="Brownsea Intranet",
        )
        return site, home

    return _make_site


def pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args):
    """Take a screenshot after every step and record it for the report."""
    page = request.getfixturevalue("page")
    if page.url == "about:blank":
        return

    index = scenario.steps.index(step)
    filename = f"{_slug(feature.rel_filename)}--{_slug(scenario.name)}--{index}.png"
    page.screenshot(path=str(SCREENSHOT_DIR / filename), full_page=True)

    entries = json.loads(SCREENSHOT_INDEX.read_text())
    key = f"{feature.rel_filename}::{scenario.name}"
    entries.setdefault(key, {})[str(index)] = filename
    SCREENSHOT_INDEX.write_text(json.dumps(entries, indent=2))
