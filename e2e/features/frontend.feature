Feature: Frontend assets
  The compiled JavaScript and CSS load on every page.

  Scenario: The home page loads without browser errors
    Given the intranet has a site
    And I am logged in
    When I visit "/"
    Then I see the heading "Home"
    And the browser reported no errors

  Scenario: The login page loads without browser errors
    Given the intranet has a site
    When I visit "/accounts/login/"
    Then I see the heading "Login to Brownsea Intranet"
    And the browser reported no errors
