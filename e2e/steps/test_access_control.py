from pytest_bdd import parsers, scenarios, when

scenarios("access_control.feature")


@when(parsers.parse('I enter the password "{password}"'))
def _enter_password(page, password):
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Continue").click()
