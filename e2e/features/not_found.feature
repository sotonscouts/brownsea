Feature: Page not found
  Visitors who follow a broken link should be told the page does not exist.

  Scenario: Visiting a URL that does not exist
    Given the intranet has a site
    When I visit "/this-page-does-not-exist/"
    Then the response status is 404
    And I see the heading "Page not found"
