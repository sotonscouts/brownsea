from pytest_bdd import parsers, scenarios, when

scenarios("authentication.feature")


@when(parsers.parse('I sign in to the admin as "{username}" with the password "{password}"'))
def _admin_sign_in(page, username, password):
    page.get_by_label("Username").fill(username)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Sign in").click()
