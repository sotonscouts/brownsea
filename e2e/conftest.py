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


@pytest.fixture(autouse=True)
def _e2e_database(transactional_db, live_server):
    """Set up the test database and the live server up front, in that order.

    Steps request fixtures dynamically, which is too late for pytest-django to guarantee the test database
    (rather than the configured one) is the one in use.
    """


@pytest.fixture(scope="session")
def base_url(live_server):
    return live_server.url


@pytest.fixture
def scenario_state():
    """Scratch space for sharing values between steps in a scenario."""
    return {}


@pytest.fixture
def make_site(live_server):
    """Replace the default Site with one that resolves to the live server."""
    from wagtail_factories import SiteFactory

    from brownsea.factories import HomePageFactory, publish

    def _make_site():
        Site.objects.all().delete()
        home = publish(HomePageFactory(parent=Page.get_first_root_node(), title="Home", slug="e2e-home"))
        host, _, port = live_server.url.removeprefix("http://").partition(":")
        return SiteFactory(
            hostname=host,
            port=int(port or 80),
            root_page=home,
            is_default_site=True,
            site_name="Brownsea Intranet",
        )

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
